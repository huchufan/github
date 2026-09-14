"""
Types for constraints
"""

from typing import Any, Protocol


class IConstraints(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
