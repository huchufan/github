"""
Types for executor
"""

from typing import Any, Protocol


class IExecutor(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
