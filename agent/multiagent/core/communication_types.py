"""
Types for communication
"""
from typing import Protocol, Any

class ICommunication(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
