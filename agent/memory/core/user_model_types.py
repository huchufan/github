"""
Types for user_model
"""
from typing import Protocol, Any

class IUserModel(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
