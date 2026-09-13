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

__all__ = ['Planner', 'TaskPlanner']
