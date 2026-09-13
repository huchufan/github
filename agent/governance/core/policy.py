"""
Governance Framework - Policy Module (compat shim + PoC)
Provides minimal PolicyCondition/PolicyLimit/PolicyValidator/PolicyViolation
and a simple Policy class for tests and imports.
"""
from typing import Any, Dict, NamedTuple, List
from dataclasses import dataclass

@dataclass
class PolicyCondition:
    # Support both old and new field names: tests may pass 'field'/'operator' or 'key'/'op'
    key: str | None = None
    op: str | None = None
    value: Any = None
    # aliases that tests may use
    field: str | None = None
    operator: str | None = None

    def __post_init__(self):
        # normalize aliases
        if self.field and not self.key:
            self.key = self.field
        if self.operator and not self.op:
            self.op = self.operator
        # final fallback: ensure key/op are strings
        if self.key is None:
            self.key = 
        if self.op is None:
            self.op = 

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

class RuleDecision:
    def __init__(self, decision: str = 'ALLOW'):
        self.decision = decision

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

# export expected names
__all__ = ['Policy', 'PolicyCondition', 'PolicyLimit', 'PolicyValidator', 'PolicyViolation', 'RuleEngine', 'ValidationResult', 'RuleDecision']
