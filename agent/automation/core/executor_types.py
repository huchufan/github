"""
Types for executor
"""
from typing import Protocol, Any

class IExecutor(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
