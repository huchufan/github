"""
多智能体框架 - 通信协议和机制 (Communication Protocol)

Agent 通信总线：消息发送、广播、订阅与 RPC 调用。

设计文档: 06_多智能体管理架构.md
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from agent.core.types import AgentMessage, RPCRequest, RPCResponse
from agent.core.errors import RPCError, RPCTimeoutError

logger = logging.getLogger(__name__)


class AgentCommunicationBus:
    """Agent 通信总线。"""

    def __init__(self):
        self.message_queue: "asyncio.Queue[AgentMessage]" = asyncio.Queue()
        self.subscribers: Dict[str, List[Dict[str, Any]]] = {}
        self.rpc_handlers: Dict[str, Callable] = {}
        self.message_buffer: Dict[str, List[AgentMessage]] = {}
        self._pending_rpc: Dict[str, "asyncio.Future"] = {}

    async def send_message(self, from_agent: str, to_agents: List[str], message_type: str, payload: Dict[str, Any]) -> List[str]:
        """发送消息。"""
        message = AgentMessage(
            from_agent=from_agent,
            to_agents=to_agents,
            message_type=message_type,
            payload=payload,
        )
        for to_agent in to_agents:
            self.message_buffer.setdefault(to_agent, []).append(message)
        await self.message_queue.put(message)
        return [message.message_id]

    async def broadcast_message(self, from_agent: str, message_type: str, payload: Dict[str, Any]) -> None:
        """广播消息。"""
        message = AgentMessage(from_agent=from_agent, to_agents=["*"], message_type=message_type, payload=payload)
        await self.message_queue.put(message)
        for handlers in self.subscribers.values():
            for entry in handlers:
                await self._dispatch(entry, message)

    async def subscribe_topic(self, agent_id: str, topic: str, handler: Callable) -> None:
        """订阅主题。"""
        self.subscribers.setdefault(topic, []).append({"agent_id": agent_id, "handler": handler})

    async def _dispatch(self, entry: Dict[str, Any], message: AgentMessage) -> None:
        try:
            result = entry["handler"](message)
            if asyncio.iscoroutine(result):
                await result
        except Exception:  # noqa: BLE001
            logger.exception("Subscriber handler failed")

    def register_rpc_handler(self, method: str, handler: Callable) -> None:
        """注册 RPC 处理器。"""
        self.rpc_handlers[method] = handler

    async def call_rpc(self, from_agent: str, to_agent: str, method: str, parameters: Dict[str, Any], timeout: int = 30) -> Any:
        """RPC 调用。"""
        if method not in self.rpc_handlers:
            raise RPCError(f"Unknown RPC method: {method}")

        request = RPCRequest(from_agent=from_agent, to_agent=to_agent, method=method, parameters=parameters)

        loop = asyncio.get_event_loop()
        future: "asyncio.Future" = loop.create_future()
        self._pending_rpc[request.request_id] = future

        try:
            # 异步执行处理器
            handler = self.rpc_handlers[method]
            result = handler(parameters)
            if asyncio.iscoroutine(result):
                result = await result
            response = RPCResponse(request_id=request.request_id, result=result)
            if not future.done():
                future.set_result(response.result)
            return response.result
        except asyncio.TimeoutError:
            raise RPCTimeoutError(f"RPC call to {to_agent}.{method} timed out")

    def receive_messages(self, agent_id: str) -> List[AgentMessage]:
        """取回某 Agent 缓冲的消息。"""
        return self.message_buffer.pop(agent_id, [])


__all__ = ["AgentCommunicationBus"]
