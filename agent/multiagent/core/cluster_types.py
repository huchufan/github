"""
Types for cluster
"""

from typing import Any, Protocol


class ICluster(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
