"""
Types for communication
"""

from typing import Any, Protocol


class ICommunication(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
