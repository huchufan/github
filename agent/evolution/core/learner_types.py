"""
Types for learner
"""

from typing import Any, Protocol


class ILearner(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
