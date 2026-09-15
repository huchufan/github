"""
自动化执行框架 - 触发管理系统 (Trigger Management)

多类型触发器：定时/事件/条件/手动/Webhook/消息/系统事件。

设计文档: 04_自动化执行框架.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (
    ExecutionContext,
    OperationStatus,
    Trigger,
    TriggerContext,
    TriggerRegistration,
    Workflow,
    WorkflowExecution,
)
from agent.core.errors import TriggerValidationError, WorkflowNotFoundError

logger = logging.getLogger(__name__)


class TriggerManager:
    """触发管理系统。"""

    TRIGGER_TYPES = {
        "schedule", "event", "condition", "manual", "webhook", "message", "system",
    }

    def __init__(self):
        self.registrations: Dict[str, TriggerRegistration] = {}
        self.triggers_by_workflow: Dict[str, List[str]] = {}

    def register_trigger(self, workflow_id: str, trigger: Trigger) -> TriggerRegistration:
        """注册触发器。"""
        validation = self.validate_trigger(trigger)
        if not validation:
            raise TriggerValidationError(f"Invalid trigger type: {trigger.trigger_type}")

        conflicts = self.detect_trigger_conflicts(workflow_id, trigger)
        if conflicts:
            logger.warning("Trigger conflicts detected: %s", conflicts)

        registration = TriggerRegistration(
            trigger_id=trigger.trigger_id,
            workflow_id=workflow_id,
            trigger=trigger,
            enabled=True,
        )
        self.registrations[trigger.trigger_id] = registration
        self.triggers_by_workflow.setdefault(workflow_id, []).append(trigger.trigger_id)
        return registration

    def validate_trigger(self, trigger: Trigger) -> bool:
        """验证触发器。"""
        return trigger.trigger_type in self.TRIGGER_TYPES

    def detect_trigger_conflicts(self, workflow_id: str, trigger: Trigger) -> List[str]:
        """检测触发器冲突（同工作流同类型重复触发）。"""
        conflicts = []
        for tid in self.triggers_by_workflow.get(workflow_id, []):
            existing = self.registrations[tid].trigger
            if existing and existing.trigger_type == trigger.trigger_type:
                conflicts.append(tid)
        return conflicts

    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        reg = self.registrations.get(trigger_id)
        return reg.trigger if reg else None

    def disable_trigger(self, trigger_id: str) -> None:
        reg = self.registrations.get(trigger_id)
        if reg:
            reg.enabled = False
            if reg.trigger:
                reg.trigger.enabled = False


class TriggerExecutor:
    """触发器执行。"""

    def __init__(self, workflow_registry: Optional[Dict[str, Workflow]] = None, execution_engine=None):
        self.workflow_registry = workflow_registry or {}
        self.execution_engine = execution_engine

    def register_workflow(self, workflow: Workflow) -> None:
        self.workflow_registry[workflow.id] = workflow

    async def execute_triggered_workflow(self, trigger: Trigger, trigger_context: TriggerContext) -> Optional[WorkflowExecution]:
        """执行被触发的工作流。"""
        if not trigger.enabled:
            logger.info("Trigger %s is disabled", trigger.trigger_id)
            return None

        workflow = self.workflow_registry.get(trigger.workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(trigger.workflow_id)

        parameters = self.prepare_workflow_parameters(trigger, trigger_context, workflow)
        can_execute = self.check_execution_conditions(workflow, parameters)
        if not can_execute:
            logger.warning("Workflow %s execution conditions not met", workflow.id)
            return None

        execution_context = ExecutionContext(
            request_id=trigger.trigger_id,
        )

        execution = WorkflowExecution(
            workflow_id=workflow.id,
            trigger_id=trigger.trigger_id,
            parameters=parameters,
        )

        if self.execution_engine is not None:
            result = await self.execution_engine.execute_workflow(workflow, execution_context)
            execution.status = result.status
            execution.result = result.result
        else:
            execution.status = OperationStatus.SUCCESS.value
            execution.result = {"parameters": parameters}

        return execution

    @staticmethod
    def prepare_workflow_parameters(trigger: Trigger, context: TriggerContext, workflow: Workflow) -> Dict[str, Any]:
        return {**trigger.config, **context.payload}

    @staticmethod
    def check_execution_conditions(workflow: Workflow, parameters: Dict[str, Any]) -> bool:
        return True


__all__ = ["TriggerManager", "TriggerExecutor"]
