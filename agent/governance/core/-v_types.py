"""
Types for -v
"""

from typing import Any, Protocol


class I_V(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
