"""
Types for analyzer
"""
from typing import Protocol, Any

class IAnalyzer(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
