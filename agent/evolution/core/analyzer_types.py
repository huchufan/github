"""
Types for analyzer
"""

from typing import Any, Protocol


class IAnalyzer(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
