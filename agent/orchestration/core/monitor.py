"""
Orchestration Framework - Monitor Module (compat shim)
Provides ExecutionMonitor and AdaptiveReplanner expected names for imports.
"""
from typing import Any, Dict, List

class ExecutionMonitor:
    def __init__(self):
        self.events = []

    def record(self, evt: Dict[str, Any]):
        self.events.append(evt)

class AdaptiveReplanner:
    def __init__(self):
        pass

__all__ = ['ExecutionMonitor', 'AdaptiveReplanner']
