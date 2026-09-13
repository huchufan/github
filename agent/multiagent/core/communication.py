"""
Multiagent Framework - Communication Module (compat shim)
Provides AgentCommunicationBus minimal implementation for imports/tests and Communication PoC.
"""
from typing import Any, Dict, List, Optional

class AgentCommunicationBus:
    def __init__(self):
        self.channels: Dict[str, List[Any]] = {}
        self._rpc_handlers: Dict[str, Any] = {}

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

    def register_rpc_handler(self, name: str, fn):
        self._rpc_handlers[name] = fn

    async def call_rpc(self, caller: str, target: str, name: str, params: Dict[str, Any]):
        if name not in self._rpc_handlers:
            raise Exception('rpc handler not found')
        fn = self._rpc_handlers[name]
        res = fn(params)
        if hasattr(res, '__await__'):
            return await res
        return res

class Communication:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"module": "communication", "ok": True}

__all__ = ['AgentCommunicationBus', 'Communication']
