"""
Types for healing
"""

from typing import Any, Protocol


class IHealing(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
