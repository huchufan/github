"""
Types for monitor
"""

from typing import Any, Protocol


class IMonitor(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
