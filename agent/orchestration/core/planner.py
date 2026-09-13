"""
Orchestration Framework - Planner Module (compat shim)
Provides TaskPlanner expected name for package imports.
"""
from typing import Any, Dict, List

class TaskPlanner:
    def __init__(self):
        self.tasks = []

    def plan(self, dag, constraints=None):
        # naive: return nodes in insertion order
        return list(dag.nodes.keys())

__all__ = ['TaskPlanner']
