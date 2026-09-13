"""
Types for dag
"""
from typing import Protocol, Any

class IDag(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
