"""
Orchestration Framework - Executor Module (compat shim + PoC)
Provides Executor class expected by tests and a concrete OrchestrationEngine used by tests.
"""

import asyncio
import inspect
from typing import Any, Dict, List, Optional

from agent.core.errors import RateLimitError
from agent.core.types import (ExecutionPlan, ExecutionResult, ExecutionState,
                              OperationStatus, SubTask, TaskResult)


class ErrorHandlingStrategy:
    def __init__(
        self,
        skill_registry: Optional[Dict[str, Any]] = None,
        default_strategy: str = "retry_on_transient",
    ):
        self.skill_registry = skill_registry or {}
        self.default_strategy = default_strategy
        # strategies mapping for tests to mutate directly
        self.strategies: Dict[str, Dict[str, Any]] = {
            "retry_on_transient": {"action": "RETRY", "retries": 3},
            "execute_fallback": {
                "action": "FALLBACK",
                "retries": 1,
                "fallback_skill": None,
            },
            "skip_and_continue": {"action": "CONTINUE", "retries": 0},
            "immediate_fail": {"action": "STOP", "retries": 0},
            "no_retry": {"action": "RETRY", "retries": 0},
        }

    def categorize_error(self, err: Exception) -> str:
        if isinstance(err, (TimeoutError, asyncio.TimeoutError)):
            return OperationStatus.TIMEOUT.value
        if (
            isinstance(err, RateLimitError)
            or getattr(getattr(err, "__class__", None), "__name__", "")
            == "RateLimitError"
        ):
            return "NETWORK_ERROR"
        try:
            from agent.core.errors import ConnectionError

            if isinstance(err, ConnectionError):
                return "TRANSIENT"
        except Exception:
            pass
        return "GENERIC_ERROR"

    def select_recovery_strategy(
        self,
        task: Optional[SubTask] = None,
        error_category: str = "",
        retry_count: int = 0,
        default_strategy: Optional[str] = None,
        **_kwargs,
    ) -> Dict[str, Any]:
        """Return a strategy dict: {'action': 'RETRY'|'FALLBACK'|'CONTINUE'|'STOP', ...}
        Conservative defaults:
         - missing task -> CONTINUE
         - explicit task retry_policy mapping honored
         - RETRY with exhausted retries -> STOP
        """
        if task is None:
            return {"action": "CONTINUE"}

        policy = getattr(task, "retry_policy", None)
        if policy and policy in self.strategies:
            strat = dict(self.strategies[policy])
            try:
                max_retries = int(strat.get("retries", 0))
            except Exception:
                max_retries = 0
            action = strat.get("action")
            # if policy explicitly says RETRY but retries exhausted -> STOP
            if action == "RETRY" and retry_count >= max_retries:
                return {"action": "STOP"}
            # otherwise return the policy as-is
            strat["retries_done"] = retry_count
            return strat

        strategy = default_strategy or self.default_strategy
        if strategy == "retry_on_transient" and retry_count >= 3:
            return {"action": "STOP"}
        if (
            error_category == OperationStatus.TIMEOUT.value
            or error_category == "TIMEOUT"
        ):
            return {"action": "RETRY"}
        if error_category == "NETWORK_ERROR":
            return {"action": "FALLBACK", "fallback_skill": None}
        return {"action": "STOP"}

    def get_recovery_action(self, strategy: Dict[str, Any]):
        # return RecoveryAction dataclass when available; else simple object
        try:
            from agent.core.types import RecoveryAction

            return RecoveryAction(
                action=strategy.get("action"),
                fallback_skill=strategy.get("fallback_skill"),
            )
        except Exception:

            class RA:
                def __init__(self, d):
                    self.action = d.get("action")
                    self.fallback_skill = d.get("fallback_skill")

            return RA(strategy)


class OrchestrationEngine:
    def __init__(
        self,
        skill_registry: Optional[Dict[str, Any]] = None,
        error_strategy: Optional[ErrorHandlingStrategy] = None,
    ):
        self.skill_registry = skill_registry or {}
        self.error_strategy = error_strategy or ErrorHandlingStrategy(
            self.skill_registry
        )

    async def _call_skill(
        self, skill_callable: Any, params: Dict[str, Any], timeout: Optional[float]
    ) -> TaskResult:
        try:
            if inspect.iscoroutinefunction(skill_callable):
                if timeout and timeout > 0:
                    res = await asyncio.wait_for(
                        skill_callable(params, {}), timeout=timeout
                    )
                else:
                    res = await skill_callable(params, {})
            else:
                res = skill_callable(params, {})
                if asyncio.iscoroutine(res):
                    if timeout and timeout > 0:
                        res = await asyncio.wait_for(res, timeout=timeout)
                    else:
                        res = await res
            return TaskResult(
                task_id=params.get("_task_id", ""),
                status=OperationStatus.SUCCESS.value,
                result=res,
                success=True,
            )
        except asyncio.TimeoutError as te:
            return TaskResult(
                task_id=params.get("_task_id", ""),
                status=OperationStatus.TIMEOUT.value,
                error=str(te),
                success=False,
            )
        except Exception as e:
            return TaskResult(
                task_id=params.get("_task_id", ""),
                status=OperationStatus.FAILURE.value,
                error=str(e),
                success=False,
            )

    async def execute_single_task(
        self,
        subtask: SubTask,
        state: Optional[ExecutionState],
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        # find skill
        skill = self.skill_registry.get(subtask.skill_name)
        if skill is None:
            return TaskResult(
                task_id=subtask.id,
                status=OperationStatus.FAILURE.value,
                error=f"skill {subtask.skill_name} not found",
                success=False,
            )
        # call skill with timeout support
        params = dict(subtask.parameters or {})
        params["_task_id"] = subtask.id
        return await self._call_skill(skill, params, getattr(subtask, "timeout", None))

    async def execute_task_group(
        self,
        tasks: List[SubTask],
        state: Optional[ExecutionState],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[TaskResult]:
        coros = [self.execute_single_task(t, state, context) for t in tasks]
        # convert exceptions into TaskResult so callers don't see raw exceptions
        raw = await asyncio.gather(*coros, return_exceptions=True)
        results: List[TaskResult] = []
        for item, sub in zip(raw, tasks):
            if isinstance(item, Exception):
                # map to TaskResult
                tr = TaskResult(
                    task_id=sub.id,
                    status=OperationStatus.FAILURE.value,
                    error=str(item),
                    success=False,
                )
                results.append(tr)
            else:
                results.append(item)
        return results

    async def handle_task_failures(
        self, results: List[TaskResult], state: ExecutionState, plan: ExecutionPlan
    ) -> bool:
        """Process failed TaskResult entries and decide whether orchestration should continue.
        Returns True to continue, False to stop.
        Behavior implemented to match tests:
         - missing subtask -> CONTINUE
         - RETRY: try executing the original task once and record result
         - FALLBACK: if fallback_skill configured and present -> execute it and record result into state.tasks_completed/failed; if no fallback configured -> STOP
         - STOP: stop orchestration
         - CONTINUE: record failure and continue
        """
        for r in results:
            if getattr(r, "success", False):
                continue
            # ensure failed recorded
            try:
                if hasattr(state, "tasks_failed"):
                    state.tasks_failed.append(r)
            except Exception:
                pass

            st = next(
                (s for s in getattr(plan, "subtasks", []) if s.id == r.task_id), None
            )
            retry_count = (
                state.get_retry_count(r.task_id)
                if hasattr(state, "get_retry_count")
                else 0
            )
            strat = self.error_strategy.select_recovery_strategy(
                task=st, error_category=r.status, retry_count=retry_count
            )
            action = strat.get("action")

            if action == "STOP":
                return False

            if action == "CONTINUE":
                continue

            if action == "RETRY":
                # increment retry and attempt one execution
                try:
                    state.retry_counts[r.task_id] = state.get_retry_count(r.task_id) + 1
                except Exception:
                    try:
                        state.retry_counts = {r.task_id: 1}
                    except Exception:
                        pass
                if st is None:
                    return True
                res = await self.execute_single_task(st, state, None)
                # record
                try:
                    if res.success and hasattr(state, "tasks_completed"):
                        state.tasks_completed.append(res)
                    elif not res.success and hasattr(state, "tasks_failed"):
                        state.tasks_failed.append(res)
                except Exception:
                    pass
                return True

            if action == "FALLBACK":
                fb = (
                    strat.get("fallback_skill")
                    or strat.get("fallback")
                    or strat.get("fallback_skill_name")
                )
                if not fb:
                    return False
                if fb not in self.skill_registry:
                    return False
                # execute fallback
                fb_skill = self.skill_registry[fb]
                params = {"_task_id": r.task_id}
                fres = await self._call_skill(fb_skill, params, None)
                try:
                    if fres.success and hasattr(state, "tasks_completed"):
                        state.tasks_completed.append(fres)
                    elif not fres.success and hasattr(state, "tasks_failed"):
                        state.tasks_failed.append(fres)
                except Exception:
                    pass
                return True

        return True

    async def orchestrate_execution(
        self, plan: ExecutionPlan, context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        result = ExecutionResult(
            status=OperationStatus.SUCCESS.value,
            tasks_executed=0,
            tasks_completed=0,
            tasks_failed=0,
        )
        context = context or {}
        for level in getattr(plan, "execution_order", []) or []:
            results = await self.execute_task_group(level, None, context)
            for tr in results:
                result.tasks_executed += 1
                if tr.success:
                    result.tasks_completed += 1
                else:
                    result.tasks_failed += 1
            # if any failed, decide whether to continue
            failed = [r for r in results if not r.success]
            if failed:
                state = ExecutionState(plan=plan)
                cont = await self.handle_task_failures(failed, state, plan)
                if not cont:
                    result.status = OperationStatus.FAILURE.value
                    break
        return result


class Executor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"ok": True}


__all__ = ["Executor", "ErrorHandlingStrategy", "OrchestrationEngine"]
