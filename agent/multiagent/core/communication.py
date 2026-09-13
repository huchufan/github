"""
Multiagent Framework - Communication Module (compat shim)
Provides AgentCommunicationBus minimal implementation for imports/tests and Communication PoC.
"""
from typing import Any, Dict, List, Optional

class AgentCommunicationBus:
    def __init__(self):
        self.channels: Dict[str, List[Any]] = {}

    def publish(self, channel: str, message: Any):
        self.channels.setdefault(channel, []).append(message)

    def subscribe(self, channel: str):
        return self.channels.get(channel, [])

class Communication:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"module": "communication", "ok": True}

__all__ = ['AgentCommunicationBus', 'Communication']
