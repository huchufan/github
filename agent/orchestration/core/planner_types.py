"""
Types for planner
"""
from typing import Protocol, Any

class IPlanner(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
