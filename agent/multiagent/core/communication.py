"""
Multiagent Framework - Communication Module (compat shim)
Provides AgentCommunicationBus minimal implementation for imports/tests.
"""
from typing import Any, Dict, List

class AgentCommunicationBus:
    def __init__(self):
        self.channels: Dict[str, List[Any]] = {}

    def publish(self, channel: str, message: Any):
        self.channels.setdefault(channel, []).append(message)

    def subscribe(self, channel: str):
        return self.channels.get(channel, [])

__all__ = ['AgentCommunicationBus']
