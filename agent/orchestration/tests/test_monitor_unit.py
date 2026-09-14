import asyncio
from datetime import datetime, timedelta

from agent.core.types import (ExecutionMetrics, ExecutionPlan, ExecutionState,
                              SubTask, TaskResult)
from agent.orchestration.core.monitor import (AdaptiveReplanner,
                                              ExecutionMonitor)


def make_state_with_plan_and_completed():
    t1 = SubTask(id="t1", skill_name="s")
    t2 = SubTask(id="t2", skill_name="s")
    plan = ExecutionPlan(
        subtasks=[t1, t2], execution_order=[[t1], [t2]], time_estimate=10
    )
    state = ExecutionState(plan=plan)
    # add completed tasks with durations
    r1 = TaskResult(task_id="t1", duration=1.0, success=True)
    r2 = TaskResult(task_id="t2", duration=2.0, success=True)
    state.tasks_completed.extend([r1, r2])
    return state


def test_calculate_metrics_basic():
    m = ExecutionMonitor()
    state = make_state_with_plan_and_completed()
    metrics = m.monitor_execution(state)
    assert isinstance(metrics, ExecutionMetrics)
    assert metrics.overall_progress >= 0
    assert metrics.success_rate == 100.0


def test_identify_bottleneck_and_estimate():
    m = ExecutionMonitor()
    state = make_state_with_plan_and_completed()
    # add a very slow completed task
    slow = TaskResult(task_id="slow", duration=40.0, success=True)
    state.tasks_completed.append(slow)
    bottlenecks = m.identify_bottleneck_tasks(state)
    assert "slow" in bottlenecks
    est = m.estimate_remaining_time(state)
    assert isinstance(est, float)


def test_detect_anomalies_timeout_and_failure_rate():
    m = ExecutionMonitor()
    # craft a state with in-progress task started long ago
    t = SubTask(id="p1", skill_name="s", timeout=0.01)
    # simulate start_time far in the past
    setattr(t, "start_time", datetime.now() - timedelta(seconds=360))
    state = ExecutionState()
    state.tasks_in_progress.append(t)
    # add completed tasks with failures to raise recent_failure_rate
    for i in range(5):
        state.tasks_completed.append(
            TaskResult(task_id=f"c{i}", duration=1.0, success=(i < 2))
        )
    anomalies = m.detect_anomalies(state)
    assert any(
        a.type == "EXCESSIVE_TIMEOUT" or a.type == "HIGH_FAILURE_RATE"
        for a in anomalies
    )


def test_adaptive_replanner_should_replan_and_generate():
    repl = AdaptiveReplanner()
    state = make_state_with_plan_and_completed()
    metrics = ExecutionMetrics()
    metrics.retry_rate = 0.5
    metrics.bottleneck_tasks = ["t1"]
    plan = state.plan
    new_plan = asyncio.run(repl.replan_if_needed(state, metrics))
    assert new_plan is not None
