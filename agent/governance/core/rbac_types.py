"""
Types for rbac
"""
from typing import Protocol, Any

class IRbac(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
