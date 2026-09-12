import asyncio
from datetime import datetime
from agent.orchestration.core.monitor import AdaptiveReplanner
from agent.core.types import ExecutionState, ExecutionPlan, SubTask, ExecutionMetrics


def make_plan():
    t1 = SubTask(id='t1', skill_name='s')
    t2 = SubTask(id='t2', skill_name='s')
    # two groups to allow reduce_parallelism behaviour
    plan = ExecutionPlan(subtasks=[t1, t2], execution_order=[[t1, t2]], time_estimate=5)
    return plan


def test_replan_not_needed_returns_none():
    repl = AdaptiveReplanner()
    state = ExecutionState(plan=make_plan(), start_time=datetime.now())
    m = ExecutionMetrics()
    m.retry_rate = 0.0
    m.bottleneck_tasks = []
    m.estimated_remaining_time = 1
    res = asyncio.run(repl.replan_if_needed(state, m))
    assert res is None


def test_replan_with_retry_rate_produces_new_plan():
    repl = AdaptiveReplanner()
    plan = make_plan()
    state = ExecutionState(plan=plan, start_time=datetime.now())
    m = ExecutionMetrics()
    m.retry_rate = 0.5
    m.bottleneck_tasks = []
    m.estimated_remaining_time = 1
    new_plan = asyncio.run(repl.replan_if_needed(state, m))
    assert new_plan is not None
    # when reduced parallelism, execution_order should be flattened to singletons
    assert all(len(level)==1 for level in new_plan.execution_order)


def test_replan_with_bottleneck_splits_or_changes():
    repl = AdaptiveReplanner()
    plan = make_plan()
    state = ExecutionState(plan=plan, start_time=datetime.now())
    m = ExecutionMetrics()
    m.retry_rate = 0.0
    m.bottleneck_tasks = ['t1']
    m.estimated_remaining_time = 1
    new_plan = asyncio.run(repl.replan_if_needed(state, m))
    assert new_plan is not None


def test_replan_handles_missing_plan_gracefully():
    repl = AdaptiveReplanner()
    state = ExecutionState(plan=None, start_time=datetime.now())
    m = ExecutionMetrics()
    m.retry_rate = 0.6
    m.bottleneck_tasks = ['t1']
    m.estimated_remaining_time = 999
    # should not raise, returns None because original plan is None
    new_plan = asyncio.run(repl.replan_if_needed(state, m))
    assert new_plan is None
