"""
Types for user_model
"""

from typing import Any, Protocol


class IUserModel(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
