"""
Types for search
"""

from typing import Any, Protocol


class ISearch(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
