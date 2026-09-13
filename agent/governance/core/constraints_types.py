"""
Types for constraints
"""
from typing import Protocol, Any

class IConstraints(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
