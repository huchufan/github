from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from agent.core.errors import AgentNotFoundError, AgentAlreadyRegisteredError
from agent.core.types import AgentState


@dataclass
class Agent:
    agent_id: str
    state: str
    role: Optional[str] = None
    capabilities: Optional[List[str]] = None
    task_count: int = 0
    current_load: float = 0.0
    available_cpu: float = 0.0
    failure_rate: float = 0.0


class AgentHealthMonitor:
    def __init__(self, lifecycle_manager: 'AgentLifecycleManager'):
        self.status: Dict[str, Dict[str, Any]] = {}
        self.manager = lifecycle_manager

    def record(self, agent_id: str, status: Dict[str, Any]):
        self.status[agent_id] = status

    async def perform_health_check(self, agent_id: str):
        # simple PoC health check
        agent = await self.manager.get_agent(agent_id)
        class Health:
            def __init__(self, overall_health: str):
                self.overall_health = overall_health

        return Health(overall_health='HEALTHY')


class AgentLifecycleManager:
    def __init__(self):
        # agents by id -> Agent
        self.agents: Dict[str, Agent] = {}

    async def create_agent(self, config: Any) -> Agent:
        # config may be AgentConfig or dict-like; create a simple Agent instance
        # assign a synthetic id if not provided
        agent_id = getattr(config, 'id', None) or getattr(config, 'agent_id', None) or f"agent_{len(self.agents)+1}"
        if agent_id in self.agents:
            raise AgentAlreadyRegisteredError(agent_id)
        role = getattr(config, 'role', None)
        caps = getattr(config, 'capabilities', None)
        agent = Agent(agent_id=agent_id, state=AgentState.INITIALIZED.value, role=role, capabilities=caps or [])
        self.agents[agent.agent_id] = agent
        return agent

    async def start_agent(self, agent_id: str):
        agent = await self.get_agent(agent_id)
        agent.state = AgentState.RUNNING.value

    async def stop_agent(self, agent_id: str):
        agent = await self.get_agent(agent_id)
        agent.state = AgentState.STOPPED.value

    async def get_agent(self, agent_id: str) -> Agent:
        a = self.agents.get(agent_id)
        if not a:
            raise AgentNotFoundError(agent_id)
        return a


class Lifecycle:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"module": "lifecycle", "ok": True}


__all__ = ['AgentLifecycleManager', 'AgentHealthMonitor', 'Lifecycle']
