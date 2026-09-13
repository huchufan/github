from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class AgentInfo:
    id: str
    role: str = 'worker'
    capabilities: List[str] = None

@dataclass
class AgentConfig:
    config: Dict[str, Any]

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}

    async def register_agent(self, info: AgentInfo):
        self.agents[info.id] = info

    async def unregister_agent(self, agent_id: str):
        if agent_id not in self.agents:
            raise Exception('not found')
        del self.agents[agent_id]

    async def discover_agents(self, role: Optional[str] = None):
        res = [a for a in self.agents.values() if (role is None or a.role == role)]
        return res

__all__ = ['AgentRegistry', 'AgentInfo', 'AgentConfig']
