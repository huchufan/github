"""
Types for policy
"""
from typing import Protocol, Any

class IPolicy(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
