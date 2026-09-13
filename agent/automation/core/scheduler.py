"""
Automation Framework - Scheduler Module (compat shim)
Provides PriorityQueue, SchedulingEngine, ResourceAwareScheduler expected names.
"""
from typing import Any, Dict, List

class PriorityQueue:
    def __init__(self):
        self.q = []

    def push(self, item):
        self.q.append(item)

    def pop(self):
        return self.q.pop(0)

class SchedulingEngine:
    def schedule(self, tasks):
        return tasks

class ResourceAwareScheduler:
    def schedule(self, tasks, resources=None):
        return tasks

__all__ = ['PriorityQueue', 'SchedulingEngine', 'ResourceAwareScheduler']
