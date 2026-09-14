"""
Types for triggers
"""

from typing import Any, Protocol


class ITriggers(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
