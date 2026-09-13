"""
Multiagent Framework - Distribution Module (compat shim)
Provides TaskDistributionManager and LoadBalancer minimal implementations for imports/tests.
Includes Distribution alias for PoC compatibility.
"""
from typing import Any, Dict, List

class LoadBalancer:
    def __init__(self, lifecycle_manager=None):
        self.workers = []
        self.lifecycle_manager = lifecycle_manager

    def register_worker(self, w: Dict[str, Any]):
        self.workers.append(w)

    def select_worker(self, job):
        # naive: return first
        return self.workers[0] if self.workers else None

    def analyze_load_distribution(self, agents):
        # return simple object with overloaded/underloaded lists
        class Dist:
            def __init__(self, overloaded, underloaded):
                self.overloaded_agents = overloaded
                self.underloaded_agents = underloaded
        overloaded = []
        underloaded = []
        for a in agents:
            avail = getattr(a, 'available_cpu', None)
            if not avail:
                # assume default available capacity 1.0 if not set
                avail = 1.0
            cur = getattr(a, 'current_load', 0)
            if cur > avail:
                overloaded.append(getattr(a, 'agent_id', None) or getattr(a, 'id', None))
            if cur < avail:
                underloaded.append(getattr(a, 'agent_id', None) or getattr(a, 'id', None))
        return Dist(overloaded, underloaded)

class TaskDistributionManager:
    def __init__(self, lifecycle_manager=None):
        self.jobs = []
        self.lifecycle_manager = lifecycle_manager

    async def distribute_task(self, task):
        # naive: find first agent with capability
        agents = await self.lifecycle_manager.get_all_agents() if self.lifecycle_manager else []
        for a in agents:
            if task.required_skills and any(s in (a.capabilities or []) for s in task.required_skills):
                # assign
                a.task_count += 1
                return a.agent_id
        return None

class Distribution:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"module": "distribution", "ok": True}

__all__ = ['TaskDistributionManager', 'LoadBalancer', 'Distribution']
