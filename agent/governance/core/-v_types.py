"""
Types for -v
"""
from typing import Protocol, Any

class I-V(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
