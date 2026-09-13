"""
Types for fusion
"""
from typing import Protocol, Any

class IFusion(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
