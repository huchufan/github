"""
Types for dag
"""

from typing import Any, Protocol


class IDag(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
