"""
Types for planner
"""

from typing import Any, Protocol


class IPlanner(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
