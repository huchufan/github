"""
Types for search
"""
from typing import Protocol, Any

class ISearch(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
