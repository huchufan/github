"""
智能编排框架 - 流程编排和执行 (Orchestration Engine)

工作流编排与执行引擎、错误处理与恢复策略。

设计文档: 02_智能编排框架设计.md
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from agent.core.types import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionState,
    OperationStatus,
    RecoveryAction,
    SubTask,
    TaskResult,
)
from agent.core.errors import ExecutionFailedError

logger = logging.getLogger(__name__)


class ErrorHandlingStrategy:
    """错误处理和恢复策略。"""

    strategies = {
        "immediate_fail": {"action": "STOP", "retries": 0},
        "retry_on_transient": {
            "action": "RETRY",
            "retries": 3,
            "backoff": "exponential",
            "transient_errors": ["TIMEOUT", "NETWORK_ERROR", "RATE_LIMIT"],
        },
        "skip_and_continue": {"action": "CONTINUE", "retries": 1, "skip_dependents": False},
        "execute_fallback": {"action": "FALLBACK", "retries": 0, "fallback_skill": "alternative_skill_name"},
        "rollback_and_notify": {"action": "ROLLBACK", "retries": 0, "notify_channels": ["email", "slack"]},
    }

    def __init__(self, default_strategy: str = "retry_on_transient"):
        self.default_strategy = default_strategy

    def categorize_error(self, error: Exception) -> str:
        """分类错误。"""
        name = type(error).__name__
        if isinstance(error, asyncio.TimeoutError) or name == "TaskTimeoutError":
            return "TIMEOUT"
        if name in ("ConnectionError", "TimeoutError", "RateLimitError"):
            return "NETWORK_ERROR"
        return "GENERIC_ERROR"

    def select_recovery_strategy(self, task: SubTask, error_category: str, retry_count: int) -> Dict[str, Any]:
        """选择恢复策略。"""
        strategy_name = task.retry_policy if task.retry_policy in self.strategies else self.default_strategy
        strategy = dict(self.strategies[strategy_name])

        if retry_count >= strategy.get("retries", 0):
            # 重试已耗尽，降级为停止或跳过
            return {"action": "STOP"}
        return strategy

    def get_recovery_action(self, strategy: Dict[str, Any]) -> RecoveryAction:
        return RecoveryAction(
            action=strategy.get("action", "STOP"),
            skip_dependents=strategy.get("skip_dependents", False),
            fallback_skill=strategy.get("fallback_skill"),
        )


class OrchestrationEngine:
    """
    工作流编排和执行引擎。

    按执行计划的层次顺序编排任务，支持同层并行执行与失败恢复。
    """

    def __init__(self, skill_registry: Optional[Dict[str, Callable]] = None, error_strategy: Optional[ErrorHandlingStrategy] = None):
        self.skill_registry = skill_registry or {}
        self.error_strategy = error_strategy or ErrorHandlingStrategy()

    def register_skill(self, name: str, fn: Callable) -> None:
        self.skill_registry[name] = fn

    def get_skill(self, name: str) -> Callable:
        if name not in self.skill_registry:
            raise KeyError(f"Skill '{name}' not registered")
        return self.skill_registry[name]

    async def orchestrate_execution(self, execution_plan: ExecutionPlan, context: Any = None) -> ExecutionResult:
        """协调任务执行。"""
        state = ExecutionState(plan=execution_plan, start_time=datetime.now())

        try:
            await self.initialize_execution_environment(context)

            for task_group in execution_plan.execution_order:
                results = await self.execute_task_group(task_group, state, context)

                if any(not r.success for r in results):
                    should_continue = await self.handle_task_failures(results, state, execution_plan)
                    if not should_continue:
                        raise ExecutionFailedError(
                            "Execution aborted due to task failures",
                            failed_tasks=state.tasks_failed,
                        )

                state.tasks_completed.extend(results)

            final_result = self.aggregate_results(state.tasks_completed)
            return ExecutionResult(
                status=OperationStatus.SUCCESS.value,
                result=final_result,
                duration=(datetime.now() - state.start_time).total_seconds(),
                tasks_executed=len(state.tasks_completed),
                tasks_completed=len([r for r in state.tasks_completed if r.success]),
                tasks_failed=len(state.tasks_failed),
            )

        except Exception as exc:
            await self.rollback_and_cleanup(state)
            return ExecutionResult(
                status=OperationStatus.FAILURE.value,
                error=str(exc),
                duration=(datetime.now() - state.start_time).total_seconds(),
                tasks_completed=len([r for r in state.tasks_completed if r.success]),
                tasks_failed=len(state.tasks_failed),
            )

    async def initialize_execution_environment(self, context: Any) -> None:
        logger.debug("Execution environment initialized")

    async def execute_task_group(self, task_group: List[SubTask], state: ExecutionState, context: Any) -> List[TaskResult]:
        """并行执行一组任务。"""
        results = await asyncio.gather(
            *(self.execute_single_task(subtask, state, context) for subtask in task_group),
            return_exceptions=True,
        )
        return [r if isinstance(r, TaskResult) else self._exception_to_result(task_group[i], r) for i, r in enumerate(results)]

    def _exception_to_result(self, task: SubTask, exc: Exception) -> TaskResult:
        return TaskResult(task_id=task.id, status=OperationStatus.FAILURE.value, error=str(exc), success=False)

    async def execute_single_task(self, subtask: SubTask, state: ExecutionState, context: Any) -> TaskResult:
        """执行单个任务。"""
        start = datetime.now()
        try:
            skill = self.get_skill(subtask.skill_name)
            parameters = subtask.parameters
            if inspect.iscoroutinefunction(skill):
                result = await asyncio.wait_for(skill(parameters, context), timeout=subtask.timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(skill, parameters, context), timeout=subtask.timeout
                )
            return TaskResult(
                task_id=subtask.id,
                status=OperationStatus.SUCCESS.value,
                result=result,
                duration=(datetime.now() - start).total_seconds(),
                success=True,
            )
        except asyncio.TimeoutError:
            return TaskResult(
                task_id=subtask.id,
                status=OperationStatus.TIMEOUT.value,
                error=f"Task exceeded timeout of {subtask.timeout}s",
                duration=(datetime.now() - start).total_seconds(),
                success=False,
            )
        except Exception as exc:
            return TaskResult(
                task_id=subtask.id,
                status=OperationStatus.FAILURE.value,
                error=str(exc),
                duration=(datetime.now() - start).total_seconds(),
                success=False,
            )

    async def handle_task_failures(self, results: List[TaskResult], state: ExecutionState, plan: ExecutionPlan) -> bool:
        """处理任务失败，返回是否继续。"""
        for result in results:
            if result.success:
                continue
            state.tasks_failed.append(result)
            state.retry_counts[result.task_id] = state.retry_counts.get(result.task_id, 0) + 1

            task = self._find_task(plan, result.task_id)
            if task is None:
                continue

            category = self.error_strategy.categorize_error(Exception(result.error or ""))
            strategy = self.error_strategy.select_recovery_strategy(task, category, state.get_retry_count(result.task_id) - 1)
            action = self.error_strategy.get_recovery_action(strategy)

            if action.action == "RETRY":
                retry_result = await self.execute_single_task(task, state, None)
                if retry_result.success:
                    state.tasks_completed.append(retry_result)
                else:
                    state.tasks_failed.append(retry_result)
            elif action.action == "CONTINUE":
                continue
            elif action.action == "FALLBACK" and action.fallback_skill:
                task.skill_name = action.fallback_skill
                fb_result = await self.execute_single_task(task, state, None)
                if fb_result.success:
                    state.tasks_completed.append(fb_result)
                else:
                    state.tasks_failed.append(fb_result)
            else:
                return False  # STOP

        return True

    @staticmethod
    def _find_task(plan: ExecutionPlan, task_id: str) -> Optional[SubTask]:
        for task in plan.subtasks:
            if task.id == task_id:
                return task
        return None

    def aggregate_results(self, results: List[TaskResult]) -> Dict[str, Any]:
        """汇总结果。"""
        return {
            "results": [r.result for r in results],
            "success_count": len([r for r in results if r.success]),
            "failure_count": len([r for r in results if not r.success]),
        }

    async def rollback_and_cleanup(self, state: ExecutionState) -> None:
        logger.debug("Rollback and cleanup completed")


__all__ = ["OrchestrationEngine", "ErrorHandlingStrategy"]
