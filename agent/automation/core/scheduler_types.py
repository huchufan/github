"""
Types for scheduler
"""

from typing import Any, Protocol


class IScheduler(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
