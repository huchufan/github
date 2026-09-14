import asyncio
from datetime import datetime, timedelta

from agent.core.types import ExecutionPlan, ExecutionState, SubTask, TaskResult
from agent.orchestration.core.monitor import (AdaptiveReplanner,
                                              ExecutionMonitor)


def make_state_with_plan_and_completed():
    # create a simple plan with two levels
    t1 = SubTask(id="t1", skill_name="s")
    t2 = SubTask(id="t2", skill_name="s")
    plan = ExecutionPlan(
        subtasks=[t1, t2], execution_order=[[t1], [t2]], time_estimate=5
    )
    state = ExecutionState(plan=plan, start_time=datetime.now())
    return state


def test_identify_bottleneck_tasks_and_avg_duration():
    monitor = ExecutionMonitor()
    state = make_state_with_plan_and_completed()
    # create completed tasks with long duration to trigger bottleneck (>30)
    tr1 = TaskResult(
        task_id="t1", status="SUCCESS", result={}, duration=40.0, success=True
    )
    tr2 = TaskResult(
        task_id="t2", status="SUCCESS", result={}, duration=5.0, success=True
    )
    state.tasks_completed = [tr1, tr2]
    # bottleneck should detect t1
    bottlenecks = monitor.identify_bottleneck_tasks(state)
    assert bottlenecks == ["t1"]
    avg = monitor.calculate_avg_duration(state.tasks_completed)
    assert avg == (40.0 + 5.0) / 2


def test_estimate_remaining_time_and_critical_path_progress():
    monitor = ExecutionMonitor()
    state = make_state_with_plan_and_completed()
    # no completed tasks -> critical path progress 0
    state.tasks_completed = []
    assert monitor.calculate_critical_path_progress(state) == 0.0
    # add one completed to make progress
    tr = TaskResult(
        task_id="t1", status="SUCCESS", result={}, duration=1.0, success=True
    )
    state.tasks_completed = [tr]
    assert monitor.calculate_critical_path_progress(state) == 50.0
    # estimate remaining time uses avg duration * remaining_levels * 60
    est = monitor.estimate_remaining_time(state)
    assert est >= 0.0


def test_detect_anomalies_timeout_and_failure_rate():
    monitor = ExecutionMonitor()
    state = make_state_with_plan_and_completed()

    # simulate in-progress task exceeding timeout
    class InProg:
        def __init__(self):
            self.id = "t_long"
            self.start_time = datetime.now() - timedelta(seconds=200)
            self.timeout = 50

    state.tasks_in_progress = [InProg()]
    # simulate recent failures to trigger HIGH_FAILURE_RATE
    tr_fail = TaskResult(
        task_id="t_prev", status="FAIL", result={}, duration=1.0, success=False
    )
    # fill tasks_completed with more than window and some failures
    state.tasks_completed = [tr_fail] * 5
    anomalies = monitor.detect_anomalies(state)
    types = [a.type for a in anomalies]
    assert "EXCESSIVE_TIMEOUT" in types or "HIGH_FAILURE_RATE" in types


def test_adaptive_replanner_should_replan_and_generate():
    repl = AdaptiveReplanner()
    state = make_state_with_plan_and_completed()

    # craft metrics-like object
    class M:
        pass

    m = M()
    m.retry_rate = 0.5
    m.bottleneck_tasks = ["t1"]
    m.estimated_remaining_time = 999
    # run replan
    new_plan = asyncio.run(repl.replan_if_needed(state, m))
    assert new_plan is not None
