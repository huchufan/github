"""
Types for audit
"""
from typing import Protocol, Any

class IAudit(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
