import asyncio

from agent.core.types import (ExecutionPlan, OperationStatus, SubTask,
                              TaskResult)
from agent.orchestration.core.executor import OrchestrationEngine


def sync_ok(params, ctx=None):
    return {"ok": True}


def sync_fail(params, ctx=None):
    raise RuntimeError("boom")


def make_subtask(id="t1", skill="s1", timeout=0.1, retry_policy="retry_on_transient"):
    return SubTask(
        id=id,
        skill_name=skill if (skill := skill) else "s1",
        timeout=timeout,
        retry_policy=retry_policy,
    )


def make_state():
    return type(
        "S",
        (),
        {
            "tasks_failed": [],
            "tasks_completed": [],
            "retry_counts": {},
            "get_retry_count": lambda self, x: self.retry_counts.get(x, 0),
        },
    )()


def test_handle_task_failures_task_missing():
    engine = OrchestrationEngine(skill_registry={"s": sync_ok})
    # plan has no subtasks
    plan = ExecutionPlan(subtasks=[])
    failed = TaskResult(
        task_id="missing",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="no task",
    )
    state = make_state()
    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert cont is True
    assert len(state.tasks_failed) == 1


def test_handle_task_failures_continue_policy():
    engine = OrchestrationEngine(skill_registry={"s": sync_ok})
    task = SubTask(id="t_continue", skill_name="s", retry_policy="skip_and_continue")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_continue",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="err",
    )
    state = make_state()
    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert cont is True
    # failed recorded, no completed
    assert len(state.tasks_failed) >= 1


def test_handle_task_failures_fallback_failure():
    engine = OrchestrationEngine(skill_registry={"orig": sync_fail, "alt": sync_fail})
    task = SubTask(id="t_fb", skill_name="orig", retry_policy="execute_fallback")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_fb",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="fail",
    )
    state = make_state()
    engine.error_strategy.strategies["execute_fallback"]["fallback_skill"] = "alt"
    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert cont is True
    # original failure + fallback failure appended
    assert len(state.tasks_failed) >= 2


def test_execute_single_task_missing_skill():
    engine = OrchestrationEngine(skill_registry={})
    sub = SubTask(id="t_miss", skill_name="not_registered", timeout=0.1)
    res = asyncio.run(engine.execute_single_task(sub, None, None))
    assert res.success is False
    assert res.status == OperationStatus.FAILURE.value
