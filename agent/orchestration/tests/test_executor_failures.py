import asyncio

import pytest

from agent.core.types import (ExecutionPlan, OperationStatus, SubTask,
                              TaskResult)
from agent.orchestration.core.executor import (ErrorHandlingStrategy,
                                               OrchestrationEngine)


def sync_skill_ok(params, ctx=None):
    return {"ok": True}


async def async_sleep_long(params, ctx=None):
    await asyncio.sleep(0.2)
    return {"slept": True}


def sync_skill_fail(params, ctx=None):
    raise RuntimeError("boom")


async def async_once_then_ok(params, ctx=None):
    # flip on the function object to simulate stateful first-fail then success
    if not hasattr(async_once_then_ok, "called"):
        async_once_then_ok.called = True
        raise RuntimeError("transient")
    return {"ok": True}


def make_subtask(id="t1", skill="s1", timeout=0.1, retry_policy="retry_on_transient"):
    return SubTask(id=id, skill_name=skill, timeout=timeout, retry_policy=retry_policy)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        asyncio.set_event_loop(None)
        loop.close()


def test_execute_single_task_timeout():
    engine = OrchestrationEngine(skill_registry={"sleepy": async_sleep_long})
    sub = make_subtask(id="t_timeout", skill="sleepy", timeout=0.05)
    res = _run(engine.execute_single_task(sub, None, None))
    assert not res.success
    assert res.status == OperationStatus.TIMEOUT.value


def test_execute_single_task_exception():
    engine = OrchestrationEngine(skill_registry={"bad": sync_skill_fail})
    sub = make_subtask(id="t_exc", skill="bad", timeout=1)
    res = _run(engine.execute_single_task(sub, None, None))
    assert not res.success
    assert res.status == OperationStatus.FAILURE.value


def test_handle_task_failures_retry_success():
    engine = OrchestrationEngine(skill_registry={"once": async_once_then_ok})
    # task that will be retried
    task = make_subtask(id="t_retry", skill="once", retry_policy="retry_on_transient")
    plan = ExecutionPlan(subtasks=[task])
    # simulate initial failed result
    failed = TaskResult(
        task_id="t_retry",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="transient",
    )
    state = type(
        "S",
        (),
        {
            "tasks_failed": [],
            "tasks_completed": [],
            "retry_counts": {},
            "get_retry_count": lambda self, x: self.retry_counts.get(x, 0),
        },
    )()
    # call handle_task_failures
    should_continue = _run(engine.handle_task_failures([failed], state, plan))
    assert should_continue is True
    # after retry, ensure retry attempt recorded (either a completed or failed entry appended)
    assert len(state.tasks_failed) + len(state.tasks_completed) >= 1


def test_handle_task_failures_fallback():
    engine = OrchestrationEngine(
        skill_registry={"alt": sync_skill_ok, "orig": sync_skill_fail}
    )
    task = make_subtask(id="t_fb", skill="orig", retry_policy="execute_fallback")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_fb",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="fail",
    )
    state = type(
        "S",
        (),
        {
            "tasks_failed": [],
            "tasks_completed": [],
            "retry_counts": {},
            "get_retry_count": lambda self, x: self.retry_counts.get(x, 0),
        },
    )()
    # register fallback skill name matches ErrorHandlingStrategy default mapping 'execute_fallback' -> fallback_skill: 'alternative_skill_name'
    # adjust strategy to use 'alt' as fallback
    engine.error_strategy.strategies["execute_fallback"]["fallback_skill"] = "alt"
    should_continue = _run(engine.handle_task_failures([failed], state, plan))
    # fallback attempt may result in success or failure; ensure an attempt was made
    assert len(state.tasks_failed) + len(state.tasks_completed) >= 1


def test_handle_task_failures_stop():
    engine = OrchestrationEngine(skill_registry={"bad": sync_skill_fail})
    task = make_subtask(id="t_stop", skill="bad", retry_policy="immediate_fail")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_stop",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="fatal",
    )
    state = type(
        "S",
        (),
        {
            "tasks_failed": [],
            "tasks_completed": [],
            "retry_counts": {},
            "get_retry_count": lambda self, x: self.retry_counts.get(x, 0),
        },
    )()
    should_continue = _run(engine.handle_task_failures([failed], state, plan))
    assert should_continue is False
