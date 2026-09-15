"""
Types for optimizer
"""

from typing import Any, Protocol


class IOptimizer(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
