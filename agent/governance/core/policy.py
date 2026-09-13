"""
Governance Framework - Policy Module (compat shim + PoC)
Provides minimal PolicyCondition/PolicyLimit/PolicyValidator/PolicyViolation
and a simple Policy class for tests and imports.
"""
from typing import Any, Dict, NamedTuple, List, Optional
from dataclasses import dataclass

from agent.core.types import Operation

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
            self.key = ''
        if self.op is None:
            self.op = ''

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
    def __init__(self):
        self.policies: List[Policy] = []

    def register_policy(self, policy: 'Policy') -> None:
        self.policies.append(policy)

    def validate_operation(self, op: Operation) -> ValidationResult:
        # check each registered policy that applies to the operation
        for pol in self.policies:
            applies = False
            if getattr(pol, 'applies_to', None):
                if op.action in pol.applies_to:
                    applies = True
            if not applies:
                continue
            # evaluate conditions: if any condition denies, return DENY
            for cond in getattr(pol, 'conditions', []):
                k = cond.key
                oper = cond.op
                val = cond.value
                if k == 'role':
                    role_val = getattr(op.actor, 'role', None)
                    if oper in ('ne', '!=') and role_val == val:
                        return ValidationResult(False, 'DENY')
                    if oper in ('eq', '==') and role_val != val:
                        return ValidationResult(False, 'DENY')
            # if no denying condition found, allow
            return ValidationResult(True, 'ALLOW')
        # default deny when no policy allows
        return ValidationResult(False, 'DENY')

class RuleEngine:
    def decide(self, input_data: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(True, 'ALLOW')

class RuleDecision:
    def __init__(self, decision: str = 'ALLOW'):
        self.decision = decision

class Policy:
    """Policy module (PoC)
    Accepts constructor args used by tests (id, name, applies_to, conditions, limits)
    """
    def __init__(self, id: str = '', name: str = '', applies_to: Optional[List[str]] = None, conditions: Optional[List[PolicyCondition]] = None, limits: Optional[List[PolicyLimit]] = None, config: Optional[Dict[str, Any]] = None, violation_severity: Optional[str] = None, condition_logic: Optional[str] = None):
        self.id = id
        self.name = name
        self.applies_to = applies_to or []
        self.conditions: List[PolicyCondition] = conditions or []
        self.limits: List[PolicyLimit] = limits or []
        self.config = config or {}
        self.violation_severity = violation_severity
        # store condition logic (AND/OR) for later evaluation
        self.condition_logic = (condition_logic or 'OR').upper()
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
