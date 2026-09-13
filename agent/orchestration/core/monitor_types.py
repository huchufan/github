"""
Types for monitor
"""
from typing import Protocol, Any

class IMonitor(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
