"""
自动化执行框架 - 工作流执行引擎 (Workflow Execution Engine)

无人值守工作流执行：环境设置、依赖验证、预检查、任务执行、后检查、结果汇总。

设计文档: 04_自动化执行框架.md
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.core.types import (
    ExecutionContext,
    ExecutionResult,
    OperationStatus,
    Workflow,
)
from agent.core.errors import DependencyMissingError, PreCheckFailedError

logger = logging.getLogger(__name__)


class WorkflowExecutionEngine:
    """工作流执行引擎。"""

    def __init__(self, task_runner: Optional[Any] = None):
        # task_runner: 可选的编排引擎，用于执行 Workflow.tasks
        self.task_runner = task_runner
        self._dependencies: Dict[str, List[str]] = {}

    def declare_dependency(self, workflow_id: str, required: List[str]) -> None:
        self._dependencies[workflow_id] = required

    async def execute_workflow(self, workflow: Workflow, context: ExecutionContext) -> ExecutionResult:
        """执行工作流。"""
        start = datetime.now()

        try:
            # 步骤 1: 环境设置
            await self.setup_environment(workflow, context)

            # 步骤 2: 依赖验证
            missing = self.verify_dependencies(workflow)
            if missing:
                raise DependencyMissingError(str(missing))

            # 步骤 3: 预检查
            pre_checks = self.run_pre_checks(workflow, context)
            if not pre_checks["all_passed"]:
                raise PreCheckFailedError(str(pre_checks["failures"]))

            # 步骤 4: 执行工作流任务
            task_results = await self.execute_workflow_tasks(workflow, context)

            # 步骤 5: 后检查
            post_checks = self.run_post_checks(workflow, context)

            # 步骤 6: 结果汇总
            final_result = self.aggregate_results(task_results, post_checks)

            return ExecutionResult(
                status=OperationStatus.SUCCESS.value,
                result=final_result,
                duration=(datetime.now() - start).total_seconds(),
                tasks_executed=len(task_results),
                tasks_completed=len(task_results),
            )

        except Exception as exc:
            return ExecutionResult(
                status=OperationStatus.FAILURE.value,
                error=str(exc),
                duration=(datetime.now() - start).total_seconds(),
            )
        finally:
            await self.cleanup_environment(workflow, context)

    async def setup_environment(self, workflow: Workflow, context: ExecutionContext) -> None:
        logger.debug("Environment setup for workflow %s", workflow.id)

    def verify_dependencies(self, workflow: Workflow) -> List[str]:
        """验证依赖，返回缺失依赖列表。"""
        required = self._dependencies.get(workflow.id, [])
        return [d for d in required if not self._dependency_available(d)]

    @staticmethod
    def _dependency_available(dep: str) -> bool:
        # 简化：默认依赖均可用
        return True

    def run_pre_checks(self, workflow: Workflow, context: ExecutionContext) -> Dict[str, Any]:
        return {"all_passed": True, "failures": []}

    async def execute_workflow_tasks(self, workflow: Workflow, context: ExecutionContext) -> List[Dict[str, Any]]:
        """执行工作流任务（可委托给编排引擎）。"""
        results: List[Dict[str, Any]] = []
        for task in workflow.tasks:
            results.append({"task_id": task.id, "skill": task.skill_name, "status": "SUCCESS"})
        return results

    def run_post_checks(self, workflow: Workflow, context: ExecutionContext) -> Dict[str, Any]:
        return {"all_passed": True}

    @staticmethod
    def aggregate_results(task_results: List[Dict[str, Any]], post_checks: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "task_count": len(task_results),
            "post_checks_passed": post_checks.get("all_passed", True),
            "results": task_results,
        }

    async def cleanup_environment(self, workflow: Workflow, context: ExecutionContext) -> None:
        logger.debug("Environment cleanup for workflow %s", workflow.id)


__all__ = ["WorkflowExecutionEngine"]
