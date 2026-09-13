"""
Multiagent Framework - Cluster Module (compat shim)
Provides AgentRegistry and ClusterScaler minimal implementations for imports/tests.
"""
from typing import Any, Dict, List

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}

    def register(self, agent_id: str, info: Dict[str, Any] = None):
        self.agents[agent_id] = info or {}

    def list_agents(self):
        return list(self.agents.keys())

class ClusterScaler:
    def __init__(self):
        self.scale = 1

    def scale_to(self, n: int):
        self.scale = n

__all__ = ['AgentRegistry', 'ClusterScaler']
