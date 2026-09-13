"""
Types for triggers
"""
from typing import Protocol, Any

class ITriggers(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
