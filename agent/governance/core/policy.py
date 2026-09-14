from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class Decision(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

@dataclass
class PolicyRule:
    id: str
    description: str
    resource_type: str
    actions: List[str]
    condition: Optional[Dict[str, Any]] = None
    effect: Decision = Decision.ALLOW

class Policy:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"ok": True}


@dataclass
class PolicyCondition:
    field: str = ""
    operator: str = "eq"
    value: Any = None

@dataclass
class PolicyLimit:
    limit_type: str = "requests"
    max_count: int = 1


@dataclass
class Policy:
    id: str = ""
    name: str = ""
    applies_to: List[str] = field(default_factory=list)
    conditions: List[PolicyCondition] = field(default_factory=list)
    limits: List[PolicyLimit] = field(default_factory=list)
    violation_severity: str = "LOW"

    def to_dict(self):
        return {"id": self.id, "name": self.name, "applies_to": self.applies_to}


@dataclass
class PolicyViolation:
    id: str = ""
    message: str = ""


@dataclass
class ValidationResult:
    allowed: bool = True
    action: str = "ALLOW"
    violations: List[PolicyViolation] = field(default_factory=list)


class RuleEngine:
    def evaluate(self, policy: Policy, op: Any) -> ValidationResult:
        for c in policy.conditions:
            # PoC: support actor.<field> simple eval
            if '.' in c.field:
                parts = c.field.split('.', 1)
                if parts[0] == 'actor':
                    val = getattr(op.actor, parts[1], None)
                else:
                    val = None
            else:
                val = getattr(op.actor, c.field, None)
            if c.operator in ("eq", "==") and str(val) != str(c.value):
                return ValidationResult(allowed=False, action="DENY", violations=[PolicyViolation(id=policy.id, message="condition failed")])
        return ValidationResult(allowed=True, action="ALLOW")


class PolicyValidator:
    def __init__(self):
        self.policies: List[Policy] = []

    def register_policy(self, policy: Policy):
        self.policies.append(policy)

    def validate_operation(self, op: Any) -> ValidationResult:
        for p in self.policies:
            if op.action in p.applies_to:
                return RuleEngine().evaluate(p, op)
        return ValidationResult(allowed=True, action="ALLOW")


# Backwards-compatible alias expected by tests
PolicyEngine = Policy
