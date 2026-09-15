"""
Types for lifecycle
"""

from typing import Any, Protocol


class ILifecycle(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
