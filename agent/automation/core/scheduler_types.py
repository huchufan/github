"""
Types for scheduler
"""
from typing import Protocol, Any

class IScheduler(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
