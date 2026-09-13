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

    # compatibility API expected by tests
    async def send_message(self, sender: str, recipients: List[str], message_type: str, payload: Dict[str, Any]):
        for r in recipients:
            self.publish(r, type('Msg', (), {'message_type': message_type, 'payload': payload}))

    def receive_messages(self, recipient: str):
        return self.channels.get(recipient, [])

class Communication:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"module": "communication", "ok": True}

__all__ = ['AgentCommunicationBus', 'Communication']
