"""
Types for policy
"""

from typing import Any, Protocol


class IPolicy(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
