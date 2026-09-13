"""
Types for lifecycle
"""
from typing import Protocol, Any

class ILifecycle(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
