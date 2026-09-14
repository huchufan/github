from datetime import datetime, timedelta

from agent.core.types import (Anomaly, ExecutionMetrics, ExecutionPlan,
                              ExecutionState, SubTask, TaskResult)
from agent.orchestration.core.monitor import (AdaptiveReplanner,
                                              ExecutionMonitor)


def make_plan():
    t1 = SubTask(id="t1", skill_name="s")
    t2 = SubTask(id="t2", skill_name="s")
    plan = ExecutionPlan(subtasks=[t1, t2], execution_order=[[t1, t2]], time_estimate=2)
    return plan


def test_monitor_execution_full_paths():
    mon = ExecutionMonitor()
    plan = make_plan()
    state = ExecutionState(plan=plan, start_time=datetime.now())
    # no completed tasks -> overall_progress 0
    state.tasks_completed = []
    state.tasks_failed = []
    state.retry_counts = {}
    state.tasks_in_progress = []
    metrics = mon.monitor_execution(state)
    assert metrics.overall_progress == 0.0

    # add completed tasks to compute success_rate and avg duration
    tr1 = TaskResult(
        task_id="t1", status="SUCCESS", result={}, duration=10.0, success=True
    )
    tr2 = TaskResult(
        task_id="t2", status="FAIL", result={}, duration=5.0, success=False
    )
    state.tasks_completed = [tr1, tr2]
    state.tasks_failed = [tr2]
    state.retry_counts = {"t1": 1, "t2": 2}
    metrics = mon.monitor_execution(state)
    assert metrics.success_rate == (1 / 2) * 100
    assert metrics.average_task_duration == (10.0 + 5.0) / 2
    # bottleneck threshold 30 -> not detected
    assert metrics.bottleneck_tasks == []

    # make a very slow task to trigger bottleneck
    tr1.duration = 40.0
    state.tasks_completed = [tr1, tr2]
    metrics = mon.monitor_execution(state)
    assert metrics.bottleneck_tasks == ["t1"]

    # tasks_in_progress exceeding timeout -> detect anomaly
    class InProg:
        def __init__(self):
            self.id = "t_long"
            self.start_time = datetime.now() - timedelta(seconds=200)
            self.timeout = 50

    state.tasks_in_progress = [InProg()]
    anomalies = mon.detect_anomalies(state)
    types = [a.type for a in anomalies]
    assert "EXCESSIVE_TIMEOUT" in types or "HIGH_FAILURE_RATE" in types

    # estimated remaining time when tasks_completed length < execution_order length
    state.tasks_completed = [tr1]
    metrics = mon.monitor_execution(state)
    assert metrics.estimated_remaining_time >= 0.0


def test_adaptive_replanner_integration():
    repl = AdaptiveReplanner()
    plan = make_plan()
    state = ExecutionState(plan=plan, start_time=datetime.now())
    m = ExecutionMetrics()
    m.retry_rate = 0.6
    m.bottleneck_tasks = ["t1"]
    m.estimated_remaining_time = 999
    new_plan = __import__("asyncio").run(repl.replan_if_needed(state, m))
    assert new_plan is not None
