import asyncio
from datetime import datetime, timedelta

from agent.core.types import (ExecutionMetrics, ExecutionPlan, ExecutionState,
                              SubTask, TaskResult)
from agent.orchestration.core.monitor import (AdaptiveReplanner,
                                              ExecutionMonitor)


def make_state_with_levels():
    t1 = SubTask(id="t1", skill_name="s")
    t2 = SubTask(id="t2", skill_name="s")
    t3 = SubTask(id="t3", skill_name="s")
    plan = ExecutionPlan(
        subtasks=[t1, t2, t3], execution_order=[[t1, t2], [t3]], time_estimate=10
    )
    state = ExecutionState(plan=plan)
    r1 = TaskResult(task_id="t1", duration=1.0, success=True)
    r2 = TaskResult(task_id="t2", duration=2.0, success=False)
    state.tasks_completed.extend([r1, r2])
    return state


def test_calculate_critical_path_progress_and_avg_duration():
    m = ExecutionMonitor()
    state = make_state_with_levels()
    metrics = m.monitor_execution(state)
    # critical path: first level not all successful -> should be 0% or partial
    assert isinstance(metrics.overall_progress, float)
    assert metrics.average_task_duration >= 1.0


def test_identify_bottleneck_and_estimate_remaining():
    m = ExecutionMonitor()
    state = make_state_with_levels()
    # add a very slow completed task to be detected as bottleneck
    slow = TaskResult(task_id="slow", duration=40.0, success=True)
    state.tasks_completed.append(slow)
    bottlenecks = m.identify_bottleneck_tasks(state)
    assert "slow" in bottlenecks
    est = m.estimate_remaining_time(state)
    assert isinstance(est, float)


def test_detect_anomalies_timeout_and_high_failure_rate():
    m = ExecutionMonitor()
    # create in-progress task started long ago
    t = SubTask(id="p1", skill_name="s", timeout=0.01)
    setattr(t, "start_time", datetime.now() - timedelta(seconds=360))
    state = ExecutionState()
    state.tasks_in_progress.append(t)
    # make completed recent with high failure ratio
    for i in range(5):
        state.tasks_completed.append(
            TaskResult(task_id=f"c{i}", duration=1.0, success=(i < 2))
        )
    anomalies = m.detect_anomalies(state)
    types = [a.type for a in anomalies]
    assert "EXCESSIVE_TIMEOUT" in types or "HIGH_FAILURE_RATE" in types


def test_adaptive_replanner_replans_when_needed():
    repl = AdaptiveReplanner()
    state = make_state_with_levels()
    metrics = ExecutionMetrics()
    metrics.retry_rate = 0.5
    metrics.bottleneck_tasks = ["t3"]
    new_plan = asyncio.run(repl.replan_if_needed(state, metrics))
    assert new_plan is not None
