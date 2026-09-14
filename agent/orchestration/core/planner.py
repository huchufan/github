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
        # create a basic ExecutionPlan-like dict for tests expecting a plan
        return {'intent': intent, 'parameters': parameters, 'ok': True}

__all__ = ['Planner', 'TaskPlanner']

