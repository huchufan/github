"""
Types for cluster
"""
from typing import Protocol, Any

class ICluster(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
