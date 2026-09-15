"""
Types for fusion
"""

from typing import Any, Protocol


class IFusion(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
