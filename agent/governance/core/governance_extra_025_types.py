"""
Types for governance_extra_025
"""
from typing import Protocol, Any

class IGovernanceExtra025(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
