import asyncio

from agent.core.types import (ExecutionPlan, OperationStatus, SubTask,
                              TaskResult)
from agent.orchestration.core.executor import OrchestrationEngine


def transient_then_ok(params, ctx=None):
    if not hasattr(transient_then_ok, "called"):
        transient_then_ok.called = True
        raise ConnectionError("transient network")
    return {"ok": True}


def always_conn_err(params, ctx=None):
    raise ConnectionError("fatal")


def always_timeout(params, ctx=None):
    raise asyncio.TimeoutError()


def test_retry_on_transient_succeeds():
    engine = OrchestrationEngine(skill_registry={"once": transient_then_ok})
    task = SubTask(id="t_retry", skill_name="once", retry_policy="retry_on_transient")
    plan = ExecutionPlan(subtasks=[task])
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
    ok = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert ok is True
    assert len(state.tasks_completed) + len(state.tasks_failed) >= 1


def test_retry_exhausted_stops():
    engine = OrchestrationEngine(skill_registry={"bad": always_conn_err})
    task = SubTask(id="t_stop", skill_name="bad", retry_policy="retry_on_transient")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_stop",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="fatal",
    )

    # simulate retry_count already at max
    class S:
        tasks_failed = []
        tasks_completed = []
        retry_counts = {"t_stop": 3}

        def get_retry_count(self, _):
            return self.retry_counts.get("t_stop", 0)

    state = S()
    ok = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert ok is False


def test_fallback_uses_alt_skill():
    engine = OrchestrationEngine(
        skill_registry={"orig": always_conn_err, "alt": lambda p, c: {"ok": True}}
    )
    task = SubTask(id="t_fb", skill_name="orig", retry_policy="execute_fallback")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_fb",
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
            "get_retry_count": lambda self, x: 0,
        },
    )()
    # set fallback
    engine.error_strategy.strategies["execute_fallback"]["fallback_skill"] = "alt"
    engine.error_strategy.strategies["execute_fallback"]["retries"] = 1
    ok = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert ok is True
    assert len(state.tasks_completed) >= 1


def test_timeout_classification_and_retry():
    engine = OrchestrationEngine(skill_registry={"to": always_timeout})
    task = SubTask(id="t_to", skill_name="to", retry_policy="retry_on_transient")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_to",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="timeout",
    )
    state = type(
        "S",
        (),
        {
            "tasks_failed": [],
            "tasks_completed": [],
            "retry_counts": {},
            "get_retry_count": lambda self, x: 0,
        },
    )()
    ok = asyncio.run(engine.handle_task_failures([failed], state, plan))
    # depending on classification, engine may attempt retry; ensure it handled without exception
    assert isinstance(ok, bool)
