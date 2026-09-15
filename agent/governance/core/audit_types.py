"""
Types for audit
"""

from typing import Any, Protocol


class IAudit(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
