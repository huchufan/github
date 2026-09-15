"""
多智能体框架 - 集群管理 (Cluster Management)

Agent 注册和发现、动态扩缩容。

设计文档: 06_多智能体管理架构.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (
    AgentConfig,
    AgentInfo,
)
from agent.core.errors import (
    AgentAlreadyRegisteredError,
    AgentNotFoundError,
    InvalidAgentInfoError,
)

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Agent 注册和发现。"""

    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.agent_by_role: Dict[str, List[str]] = {}
        self.agent_by_capability: Dict[str, List[str]] = {}
        self.events: List[Dict[str, Any]] = []

    def validate_agent_info(self, info: AgentInfo) -> bool:
        return bool(info.id and info.role)

    async def register_agent(self, agent_info: AgentInfo) -> None:
        """注册 Agent。"""
        if not self.validate_agent_info(agent_info):
            raise InvalidAgentInfoError("Invalid agent information")
        if agent_info.id in self.agents:
            raise AgentAlreadyRegisteredError(f"Agent {agent_info.id} already registered")

        self.agents[agent_info.id] = agent_info
        self.agent_by_role.setdefault(agent_info.role, []).append(agent_info.id)
        for capability in agent_info.capabilities:
            self.agent_by_capability.setdefault(capability, []).append(agent_info.id)
        await self.broadcast_event("AGENT_REGISTERED", agent_info)

    async def discover_agents(
        self,
        role: Optional[str] = None,
        capability: Optional[str] = None,
        specialization: Optional[str] = None,
    ) -> List[AgentInfo]:
        """发现 Agent。"""
        candidates = list(self.agents.values())
        if role:
            candidates = [a for a in candidates if a.role == role]
        if capability:
            candidates = [a for a in candidates if capability in a.capabilities]
        if specialization:
            candidates = [a for a in candidates if a.specialization == specialization]
        return [a for a in candidates if a.state == "RUNNING"]

    async def unregister_agent(self, agent_id: str) -> None:
        """注销 Agent。"""
        info = self.agents.pop(agent_id, None)
        if info is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        if info.role in self.agent_by_role and agent_id in self.agent_by_role[info.role]:
            self.agent_by_role[info.role].remove(agent_id)
        for capability in info.capabilities:
            if capability in self.agent_by_capability and agent_id in self.agent_by_capability[capability]:
                self.agent_by_capability[capability].remove(agent_id)
        await self.broadcast_event("AGENT_UNREGISTERED", info)

    async def broadcast_event(self, event_type: str, info: AgentInfo) -> None:
        self.events.append({"type": event_type, "agent_id": info.id})


class ClusterScaler:
    """集群动态扩缩容。"""

    def __init__(self, lifecycle=None, registry: Optional[AgentRegistry] = None):
        self.lifecycle = lifecycle
        self.registry = registry
        self.scale_log: List[Dict[str, Any]] = []

    async def analyze_cluster_metrics(self) -> Dict[str, float]:
        """分析集群状态。"""
        if self.lifecycle is None:
            return {"avg_load": 0.0, "avg_response_time": 0.0}
        agents = await self.lifecycle.get_all_agents()
        if not agents:
            return {"avg_load": 0.0, "avg_response_time": 0.0}
        return {
            "avg_load": sum(a.current_load for a in agents) / len(agents),
            "avg_response_time": sum(a.avg_response_time for a in agents) / len(agents),
        }

    async def scale_up(self, count: int = 1) -> List[str]:
        """扩容：添加新 Agent。"""
        created = []
        for _ in range(count):
            config = AgentConfig(role="WORKER", capabilities=["task_execution"])
            if self.lifecycle:
                agent = await self.lifecycle.create_agent(config)
                await self.lifecycle.start_agent(agent.agent_id)
                created.append(agent.agent_id)
                self.scale_log.append({"action": "scale_up", "agent_id": agent.agent_id})
        return created

    async def scale_down(self, count: int = 1) -> List[str]:
        """缩容：移除负载最低的 Agent。"""
        if self.lifecycle is None:
            return []
        agents = await self.lifecycle.get_all_agents()
        agents_by_load = sorted(agents, key=lambda a: a.current_load)
        removed = []
        for agent in agents_by_load[:count]:
            if agent.current_load > 0:
                continue
            await self.lifecycle.stop_agent(agent.agent_id)
            removed.append(agent.agent_id)
            self.scale_log.append({"action": "scale_down", "agent_id": agent.agent_id})
        return removed


__all__ = ["AgentRegistry", "ClusterScaler"]
