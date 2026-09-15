"""
Types for distiller
"""

from typing import Any, Protocol


class IDistiller(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
