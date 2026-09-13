"""
Governance Framework - Constraints Module (compat shim)
Provides minimal ConstraintViolation/ConstraintCheckResult/ExecutionConstraints/ResourceQuotaManager
for imports and lightweight tests. Also exposes Constraints PoC used by some tests.
"""
from dataclasses import dataclass
from typing import List, Any, Dict

@dataclass
class ConstraintViolation:
    reason: str

@dataclass
class ConstraintCheckResult:
    ok: bool
    violations: List[ConstraintViolation]

class ExecutionConstraints:
    def __init__(self):
        self.limits = {}

class ResourceQuotaManager:
    def __init__(self):
        self.usage = {}

class Constraints:
    def __init__(self):
        self.checks = []
        # expose a simple config dict expected by tests
        self.config: Dict[str, Any] = {}

    def check(self, ctx: Dict[str, Any]) -> ConstraintCheckResult:
        return ConstraintCheckResult(ok=True, violations=[])

__all__ = ['ConstraintViolation', 'ConstraintCheckResult', 'ExecutionConstraints', 'ResourceQuotaManager', 'Constraints']
