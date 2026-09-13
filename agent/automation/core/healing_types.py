"""
Types for healing
"""
from typing import Protocol, Any

class IHealing(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
