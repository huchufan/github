"""
Orchestration Framework - Executor Module (compat shim)
Provides OrchestrationEngine and ErrorHandlingStrategy expected names for imports.
"""
from typing import Any, Dict

class ErrorHandlingStrategy:
    def __init__(self, strategy: str = 'retry'):
        self.strategy = strategy

class OrchestrationEngine:
    def __init__(self):
        self.state = {}

    def run(self, dag, planner, executor):
        # naive orchestration: call executor.execute() for each node
        results = {}
        for nid in dag.nodes:
            results[nid] = executor.execute(nid)
        return results

__all__ = ['OrchestrationEngine', 'ErrorHandlingStrategy']
