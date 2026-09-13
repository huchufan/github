"""
Types for optimizer
"""
from typing import Protocol, Any

class IOptimizer(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
