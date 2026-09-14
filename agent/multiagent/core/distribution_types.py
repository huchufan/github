"""
Types for distribution
"""

from typing import Any, Protocol


class IDistribution(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
