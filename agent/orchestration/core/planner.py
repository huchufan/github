"""
Orchestration Framework - Planner Module (compat shim + PoC)
Provides Planner and TaskPlanner names for imports.
"""
from typing import Any, Dict, List

class Planner:
    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

    def execute_plan(self, dag):
        return list(dag.nodes.keys())

    def execute(self):
        # backward-compatible execute used in tests
        return {"ok": True}

class TaskPlanner:
    def __init__(self):
        self.tasks = []

    def plan(self, dag, constraints=None):
        # naive: return nodes in insertion order
        return list(dag.nodes.keys())

    def execute(self):
        # backward-compatible execute used in tests
        return {"ok": True}

class TaskPlanner:
    def __init__(self):
        self.tasks = []

    def plan(self, dag, constraints=None):
        # naive: return nodes in insertion order
        return list(dag.nodes.keys())

    def plan_execution(self, intent, parameters):
        # create a basic ExecutionPlan object for tests expecting a plan
        from agent.core.types import ExecutionPlan, SubTask
        subtasks = [SubTask(id=f"{i}", skill_name=s) for i, s in enumerate(getattr(intent, 'skills_involved', []), start=1)]
        # estimate time as 60s per skill by default
        time_estimate = len(subtasks) * 60.0
        plan = ExecutionPlan(intent=intent, subtasks=subtasks, execution_order=[[t for t in subtasks]], time_estimate=time_estimate)
        return plan

__all__ = ['Planner', 'TaskPlanner']

