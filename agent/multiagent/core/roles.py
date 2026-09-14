"""
多智能体框架 - Agent 角色和职责 (Roles & Duties)

角色定义、角色分配与协调者选举。

设计文档: 06_多智能体管理架构.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.errors import (InsufficientCapabilityError,
                               NoAvailableAgentError, RoleLimitExceededError)
from agent.core.types import Agent, AgentConfig

logger = logging.getLogger(__name__)


ROLE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "COORDINATOR": {
        "description": "协调集群中其他 Agent 的工作",
        "count_per_cluster": 3,
        "required_capabilities": ["global_view", "task_decomposition"],
    },
    "WORKER": {
        "description": "执行具体的任务",
        "count_per_cluster": 1000,  # flexible
        "required_capabilities": ["task_execution"],
    },
    "SPECIALIST": {
        "description": "在特定领域提供专业能力",
        "count_per_cluster": 1000,
        "required_capabilities": [],
    },
    "MONITOR": {
        "description": "监控集群的整体健康和性能",
        "count_per_cluster": 2,
        "required_capabilities": ["monitoring"],
    },
    "LEARNER": {
        "description": "从集群学习和优化",
        "count_per_cluster": 2,
        "required_capabilities": ["data_analysis"],
    },
}


class AgentRoleManager:
    """Agent 角色管理。"""

    def __init__(self, lifecycle=None):
        self.lifecycle = lifecycle
        self.coordinator_id: Optional[str] = None

    def get_role_definition(self, role: str) -> Dict[str, Any]:
        return ROLE_DEFINITIONS.get(
            role, {"count_per_cluster": 1000, "required_capabilities": []}
        )

    def verify_agent_capabilities(
        self, agent: Agent, role_definition: Dict[str, Any]
    ) -> bool:
        """验证 Agent 能力。"""
        required = role_definition.get("required_capabilities", [])
        return all(c in agent.capabilities for c in required)

    async def count_agents_with_role(self, role: str) -> int:
        if self.lifecycle is None:
            return 0
        agents = await self.lifecycle.get_all_agents()
        return sum(1 for a in agents if a.role == role)

    async def assign_role(
        self, agent: Agent, role: str, specialization: Optional[str] = None
    ) -> Agent:
        """为 Agent 分配角色。"""
        role_definition = self.get_role_definition(role)

        if not self.verify_agent_capabilities(agent, role_definition):
            raise InsufficientCapabilityError(
                f"Agent {agent.agent_id} does not have required capabilities for role {role}"
            )

        current_count = await self.count_agents_with_role(role)
        if current_count >= role_definition["count_per_cluster"]:
            raise RoleLimitExceededError(f"Role {role} has reached maximum count")

        agent.role = role
        agent.specialization = specialization or ""
        if role == "COORDINATOR":
            self.coordinator_id = agent.agent_id
        return agent

    async def elect_coordinator(self, agents: List[Agent]) -> Agent:
        """选举协调者。"""
        if not agents:
            raise NoAvailableAgentError("No available agents for coordinator election")

        scores = {}
        for agent in agents:
            score = 0.0
            score += agent.available_cpu * 0.3
            score += agent.available_memory * 0.3
            score += min(agent.uptime / 3600, 10) * 0.2
            score += (1 - agent.failure_rate) * 0.2
            scores[agent.agent_id] = score

        elected_id = max(scores, key=scores.get)
        elected = next(a for a in agents if a.agent_id == elected_id)
        await self.assign_role(elected, "COORDINATOR")
        return elected


__all__ = ["AgentRoleManager", "ROLE_DEFINITIONS"]
