"""
Automation Framework - Triggers Module (compat shim)
Provides TriggerManager and TriggerExecutor minimal implementations for imports/tests.
"""
from typing import Any, Dict, List

class TriggerExecutor:
    def __init__(self):
        pass

    def run(self, trigger):
        return {"ok": True}

class TriggerManager:
    def __init__(self):
        self.triggers: List[Dict[str, Any]] = []

    def register(self, t: Dict[str, Any]):
        self.triggers.append(t)

__all__ = ['TriggerManager', 'TriggerExecutor']
