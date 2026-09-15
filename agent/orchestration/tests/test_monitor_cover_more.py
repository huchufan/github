from datetime import datetime

from agent.core.types import (ExecutionMetrics, ExecutionPlan, ExecutionState,
                              SubTask, TaskResult)
from agent.orchestration.core.monitor import (AdaptiveReplanner,
                                              ExecutionMonitor)


def make_plan_levels(levels_counts):
    # helper to make plan with execution_order based on list of counts per level
    subtasks = []
    execution_order = []
    idx = 1
    for cnt in levels_counts:
        level = []
        for _ in range(cnt):
            t = SubTask(id=f"t{idx}", skill_name="s")
            subtasks.append(t)
            level.append(t)
            idx += 1
        execution_order.append(level)
    return ExecutionPlan(
        subtasks=subtasks, execution_order=execution_order, time_estimate=10
    )


def make_state_with(plan=None):
    return ExecutionState(plan=plan, start_time=datetime.now())


def test_calculate_parallelism_efficiency_varied():
    monitor = ExecutionMonitor()
    # plan with 2 levels, first level width 3
    plan = make_plan_levels([3, 1])
    state = make_state_with(plan)
    # no completed -> efficiency 0
    state.tasks_completed = []
    assert monitor.calculate_parallelism_efficiency(state) == 0.0
    # mark one task completed -> small efficiency but >0
    tr = TaskResult(
        task_id="t1", status="SUCCESS", result={}, duration=1.0, success=True
    )
    state.tasks_completed = [tr]
    eff = monitor.calculate_parallelism_efficiency(state)
    assert 0.0 <= eff <= 1.0


def test_identify_bottleneck_threshold_and_none():
    monitor = ExecutionMonitor()
    plan = make_plan_levels([1])
    state = make_state_with(plan)
    # durations below threshold -> no bottleneck
    tr = TaskResult(
        task_id="t1", status="SUCCESS", result={}, duration=10.0, success=True
    )
    state.tasks_completed = [tr]
    assert monitor.identify_bottleneck_tasks(state) == []
    # duration above threshold
    tr2 = TaskResult(
        task_id="t1", status="SUCCESS", result={}, duration=40.0, success=True
    )
    state.tasks_completed = [tr2]
    assert monitor.identify_bottleneck_tasks(state) == ["t1"]


def test_calculate_retry_rate_and_recent_failure_rate():
    monitor = ExecutionMonitor()
    plan = make_plan_levels([1])
    state = make_state_with(plan)
    state.retry_counts = {"t1": 2, "t2": 1}
    # set tasks completed and failed counts
    ok = TaskResult(
        task_id="t1", status="SUCCESS", result={}, duration=1.0, success=True
    )
    fail = TaskResult(
        task_id="t2", status="FAIL", result={}, duration=1.0, success=False
    )
    state.tasks_completed = [ok]
    state.tasks_failed = [fail]
    rr = monitor.calculate_retry_rate(state)
    assert rr >= 0.0
    # recent failure rate uses last window slice; ensure not divide by zero
    recent = monitor._recent_failure_rate(state, window=10)
    assert 0.0 <= recent <= 1.0


def test_adaptive_replanner_should_replan_variants():
    repl = AdaptiveReplanner()
    # plan with small time_estimate
    plan = make_plan_levels([1, 1])
    state = ExecutionState(plan=plan, start_time=datetime.now())
    metrics = ExecutionMetrics()
    # case 1: retry_rate triggers
    metrics.retry_rate = 0.4
    metrics.bottleneck_tasks = []
    metrics.estimated_remaining_time = 1
    assert repl.should_replan(state, metrics) is True
    # case 2: bottleneck triggers
    metrics.retry_rate = 0.0
    metrics.bottleneck_tasks = ["t1"]
    assert repl.should_replan(state, metrics) is True
    # case 3: estimated remaining time triggers
    metrics.bottleneck_tasks = []
    metrics.estimated_remaining_time = state.plan.time_estimate * 3
    assert repl.should_replan(state, metrics) is True
