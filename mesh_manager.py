"""Mesh manager - basic mesh/cluster manager utilities (minimal implementation for tests)

Provides agent registration, heartbeat tracking, simple rebalance heuristic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class MeshAgent:
    agent_id: str
    role: str = "worker"
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now())
    state: str = "RUNNING"
    load: float = 0.0


class MeshManager:
    def __init__(self):
        self.agents: Dict[str, MeshAgent] = {}

    def register_agent(self, agent_id: str, role: str = "worker") -> MeshAgent:
        agent = MeshAgent(agent_id=agent_id, role=role)
        self.agents[agent_id] = agent
        return agent

    def unregister_agent(self, agent_id: str) -> bool:
        return self.agents.pop(agent_id, None) is not None

    def get_agent(self, agent_id: str) -> Optional[MeshAgent]:
        return self.agents.get(agent_id)

    def list_agents(self) -> List[MeshAgent]:
        return list(self.agents.values())

    def heartbeat(self, agent_id: str) -> bool:
        a = self.agents.get(agent_id)
        if not a:
            return False
        a.last_heartbeat = datetime.now()
        return True

    def mark_dead_if_stale(self, stale_after: timedelta = timedelta(seconds=60)) -> List[str]:
        now = datetime.now()
        dead = []
        for aid, a in list(self.agents.items()):
            if now - a.last_heartbeat > stale_after:
                a.state = "DEAD"
                dead.append(aid)
        return dead

    def rebalance_load(self) -> Dict[str, float]:
        # naive rebalance: set each agent's load to average
        if not self.agents:
            return {}
        avg = sum(a.load for a in self.agents.values()) / len(self.agents)
        for a in self.agents.values():
            a.load = avg
        return {a.agent_id: a.load for a in self.agents.values()}
