"""
Automation Framework - Executor Module (compat shim + PoC)
Provides WorkflowExecutionEngine expected by package imports and a PoC Executor.
"""

from typing import Any, Dict, Optional


class Executor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs) -> Any:
        return {"ok": True}


class WorkflowExecutionEngine:
    def __init__(self):
        pass

    async def execute_workflow(self, workflow, ctx=None):
        class Result:
            def __init__(self):
                self.status = "SUCCESS"
                self.tasks_executed = len(
                    getattr(workflow, "tasks", []) if workflow else []
                )

        return Result()

    def declare_dependency(self, name, deps):
        # no-op compatibility
        return None


__all__ = ["Executor", "WorkflowExecutionEngine"]
