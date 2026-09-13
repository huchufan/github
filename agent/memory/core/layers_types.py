"""
Types for layers
"""
from typing import Protocol, Any

class ILayers(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
