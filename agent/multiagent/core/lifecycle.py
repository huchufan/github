"""
Multiagent Framework - Lifecycle Module (compat shim)
Provides AgentLifecycleManager and AgentHealthMonitor minimal implementations for imports/tests.
"""
from typing import Any, Dict, List

class AgentHealthMonitor:
    def __init__(self):
        self.status = {}

    def record(self, agent_id: str, status: Dict[str, Any]):
        self.status[agent_id] = status

class AgentLifecycleManager:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_id: str, meta: Dict[str, Any] = None):
        self.agents[agent_id] = meta or {}

    def get_agent(self, agent_id: str):
        return self.agents.get(agent_id)

__all__ = ['AgentLifecycleManager', 'AgentHealthMonitor']
