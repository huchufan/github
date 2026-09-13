"""
Multiagent Framework - Distribution Module (compat shim)
Provides TaskDistributionManager and LoadBalancer minimal implementations for imports/tests.
Includes Distribution alias for PoC compatibility.
"""
from typing import Any, Dict, List

class LoadBalancer:
    def __init__(self):
        self.workers = []

    def register_worker(self, w: Dict[str, Any]):
        self.workers.append(w)

    def select_worker(self, job):
        # naive: return first
        return self.workers[0] if self.workers else None

class TaskDistributionManager:
    def __init__(self):
        self.jobs = []

    def distribute(self, job, workers):
        wb = LoadBalancer()
        for w in workers:
            wb.register_worker(w)
        return wb.select_worker(job)

class Distribution:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"module": "distribution", "ok": True}

__all__ = ['TaskDistributionManager', 'LoadBalancer', 'Distribution']
