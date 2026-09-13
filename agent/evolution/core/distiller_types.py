"""
Types for distiller
"""
from typing import Protocol, Any

class IDistiller(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
