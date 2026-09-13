"""
Governance Framework - Constraints Module (compat shim)
Provides minimal ConstraintViolation/ConstraintCheckResult/ExecutionConstraints/ResourceQuotaManager
for imports and lightweight tests.
"""
from dataclasses import dataclass
from typing import List, Any

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

__all__ = ['ConstraintViolation', 'ConstraintCheckResult', 'ExecutionConstraints', 'ResourceQuotaManager']
