"""
Types for distribution
"""
from typing import Protocol, Any

class IDistribution(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
