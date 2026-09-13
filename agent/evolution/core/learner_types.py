"""
Types for learner
"""
from typing import Protocol, Any

class ILearner(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
