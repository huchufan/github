"""
Governance Framework - Policy Module (compat shim)
Provides minimal PolicyCondition/PolicyLimit/PolicyValidator/PolicyViolation/RuleEngine/ValidationResult
names expected by package imports. Lightweight for tests and imports.
"""
from typing import Any, Dict, List, NamedTuple
from dataclasses import dataclass

@dataclass
class PolicyCondition:
    key: str
    op: str
    value: Any

@dataclass
class PolicyLimit:
    name: str
    limit: int

@dataclass
class PolicyViolation:
    reason: str

class ValidationResult(NamedTuple):
    allowed: bool
    action: str = 'ALLOW'

class PolicyValidator:
    def validate(self, ctx: Dict[str, Any]) -> ValidationResult:
        # trivial validator: allow everything
        return ValidationResult(True, 'ALLOW')

class RuleEngine:
    def decide(self, input_data: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(True, 'ALLOW')

__all__ = ['PolicyCondition', 'PolicyLimit', 'PolicyValidator', 'PolicyViolation', 'RuleEngine', 'ValidationResult']
