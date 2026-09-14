"""
Types for rbac
"""

from typing import Any, Protocol


class IRbac(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
