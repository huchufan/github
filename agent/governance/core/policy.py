"""
Governance Framework - Policy Module (compat shim + PoC)
Provides minimal PolicyCondition/PolicyLimit/PolicyValidator/PolicyViolation
and a simple Policy class for tests and imports.
"""
from typing import Any, Dict, NamedTuple, List
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

class Policy:
    """Policy module (PoC)
    """
    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.conditions: List[PolicyCondition] = []
        self.limits: List[PolicyLimit] = []
        self.validator = PolicyValidator()

    def add_condition(self, cond: PolicyCondition):
        self.conditions.append(cond)

    def add_limit(self, lim: PolicyLimit):
        self.limits.append(lim)

    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Placeholder execute"""
        return {"module": "policy", "ok": True}

__all__ = ['Policy', 'PolicyCondition', 'PolicyLimit', 'PolicyValidator', 'PolicyViolation', 'RuleEngine', 'ValidationResult']
