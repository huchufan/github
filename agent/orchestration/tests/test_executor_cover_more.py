import asyncio

import pytest

from agent.core.types import (ExecutionPlan, ExecutionState, OperationStatus,
                              SubTask, TaskResult)
from agent.orchestration.core.executor import (ErrorHandlingStrategy,
                                               OrchestrationEngine)


def test_select_recovery_strategy_fallback_allowed_when_retries_exhausted():
    strat = ErrorHandlingStrategy()
    # ensure strategy exists
    strat.strategies["execute_fallback"] = {
        "action": "FALLBACK",
        "retries": 0,
        "fallback_skill": "alt",
    }
    task = SubTask(id="t1", skill_name="orig", retry_policy="execute_fallback")
    # retry_count >= retries: should still return FALLBACK
    chosen = strat.select_recovery_strategy(
        task, error_category="GENERIC_ERROR", retry_count=0
    )
    assert chosen.get("action") == "FALLBACK"
    assert chosen.get("fallback_skill") == "alt"


def test_select_recovery_strategy_returns_stop_when_retries_exhausted_and_not_fallback():
    strat = ErrorHandlingStrategy()
    strat.strategies["no_retry"] = {"action": "RETRY", "retries": 0}
    task = SubTask(id="t2", skill_name="orig", retry_policy="no_retry")
    chosen = strat.select_recovery_strategy(
        task, error_category="GENERIC_ERROR", retry_count=0
    )
    assert chosen.get("action") == "STOP"


def test_handle_task_failures_fallback_executes_alt_skill():
    # orig fails, alt succeeds
    def orig(params, ctx):
        raise RuntimeError("orig fail")

    def alt(params, ctx):
        return {"ok": True}

    engine = OrchestrationEngine(skill_registry={"orig": orig, "alt": alt})
    task = SubTask(id="t_fb", skill_name="orig", retry_policy="execute_fallback")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_fb",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="fail",
    )
    state = ExecutionState(plan=plan)
    # configure fallback
    engine.error_strategy.strategies["execute_fallback"]["fallback_skill"] = "alt"

    # run coroutine synchronously to avoid pytest-asyncio dependency
    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert cont is True
    # check that a completed result from fallback was appended
    assert any(r.success for r in state.tasks_completed)


def test_handle_task_failures_stop_on_non_recoverable():
    # orig fails, no fallback configured -> stop
    def orig(params, ctx):
        raise RuntimeError("orig fail")

    engine = OrchestrationEngine(skill_registry={"orig": orig})
    task = SubTask(id="t_stop", skill_name="orig", retry_policy="immediate_fail")
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(
        task_id="t_stop",
        status=OperationStatus.FAILURE.value,
        success=False,
        error="fatal",
    )
    state = ExecutionState(plan=plan)

    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert cont is False
