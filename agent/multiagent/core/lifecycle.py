"""
多智能体框架 - Agent 生命周期管理 (Lifecycle Management)

Agent 创建/启动/停止、心跳监控与健康检查。

设计文档: 06_多智能体管理架构.md
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.core.types import (
    Agent,
    AgentConfig,
    AgentHealthStatus,
    AgentHeartbeat,
    AgentState,
)
from agent.core.errors import AgentStateError, AgentNotFoundError

logger = logging.getLogger(__name__)


class AgentLifecycleManager:
    """Agent 生命周期管理。"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    async def create_agent(self, agent_config: AgentConfig) -> Agent:
        """创建 Agent。"""
        agent = Agent(config=agent_config, state=AgentState.CREATED.value)
        agent.capabilities = list(agent_config.capabilities)
        self.agents[agent.agent_id] = agent
        agent.state = AgentState.INITIALIZED.value
        return agent

    async def get_agent(self, agent_id: str) -> Agent:
        if agent_id not in self.agents:
            raise AgentNotFoundError(agent_id)
        return self.agents[agent_id]

    async def get_all_agents(self) -> List[Agent]:
        return list(self.agents.values())

    async def start_agent(self, agent_id: str) -> Agent:
        """启动 Agent。"""
        agent = await self.get_agent(agent_id)
        if agent.state not in [AgentState.INITIALIZED.value, AgentState.PAUSED.value, AgentState.STOPPED.value]:
            raise AgentStateError(f"Cannot start agent in state {agent.state}")
        agent.state = AgentState.RUNNING.value
        agent.started_at = datetime.now()
        return agent

    async def stop_agent(self, agent_id: str, graceful: bool = True) -> Agent:
        """停止 Agent。"""
        agent = await self.get_agent(agent_id)
        agent.state = AgentState.STOPPING.value
        agent.state = AgentState.STOPPED.value
        agent.stopped_at = datetime.now()
        return agent

    async def handle_agent_failure(self, agent_id: str) -> Agent:
        """处理 Agent 故障。"""
        agent = await self.get_agent(agent_id)
        agent.state = AgentState.FAILED.value
        return agent

    async def monitor_agent_health(self, resource_threshold: Dict[str, float] | None = None) -> List[str]:
        """监控 Agent 健康状态，返回被标记为 DEGRADED 的 agent id。"""
        thresholds = resource_threshold or {"cpu": 95, "memory": 90}
        degraded = []
        for agent in self.agents.values():
            if agent.state == AgentState.RUNNING.value:
                if agent.cpu_usage > thresholds["cpu"] or agent.memory_usage > thresholds["memory"]:
                    agent.state = AgentState.DEGRADED.value
                    degraded.append(agent.agent_id)
        return degraded


class AgentHealthMonitor:
    """Agent 健康监控。"""

    def __init__(self, lifecycle: Optional[AgentLifecycleManager] = None):
        self.lifecycle = lifecycle or AgentLifecycleManager()
        self.last_heartbeat: Dict[str, datetime] = {}

    async def send_heartbeat(self, agent_id: str, heartbeat: AgentHeartbeat) -> AgentHeartbeat:
        """记录一次心跳。"""
        self.last_heartbeat[agent_id] = datetime.now()
        return heartbeat

    def check_heartbeat(self, agent_id: str, timeout_seconds: int = 60) -> bool:
        """检查心跳是否存活。"""
        last = self.last_heartbeat.get(agent_id)
        if last is None:
            return False
        return (datetime.now() - last).total_seconds() < timeout_seconds

    async def perform_health_check(self, agent_id: str) -> AgentHealthStatus:
        """执行完整的健康检查。"""
        agent = await self.lifecycle.get_agent(agent_id)
        status = AgentHealthStatus(agent_id=agent_id)
        status.connectivity = agent.state == AgentState.RUNNING.value
        status.resource_usage = {"cpu": agent.cpu_usage, "memory": agent.memory_usage}
        status.queue_status = {"task_count": agent.task_count}
        status.error_rate = agent.failure_rate
        status.response_time = agent.avg_response_time
        status.overall_health = "HEALTHY" if status.connectivity else "UNHEALTHY"
        return status


__all__ = ["AgentLifecycleManager", "AgentHealthMonitor"]
