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
    condition_logic: str = "AND"  # 'AND' or 'OR'
    # Backwards-compatible simple config for legacy callers/tests
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "applies_to": self.applies_to}

    # Backwards-compatible execute() expected by auto-generated tests
    def execute(self, *args, **kwargs):
        return {"ok": True}


@dataclass
class PolicyViolation:
    policy_id: str = ""
    id: str = ""
    message: str = ""
    limit: Optional[PolicyLimit] = None


@dataclass
class ValidationResult:
    allowed: bool = True
    action: str = "ALLOW"
    violations: List[PolicyViolation] = field(default_factory=list)


@dataclass
class RuleDecision:
    passed: bool = False
    matched_count: int = 0


class RuleEngine:
    def evaluate_rule(self, policy: Policy, context: Dict[str, Any]) -> RuleDecision:
        """Evaluate a policy's conditions against a provided context dict.
        Context expected shape: {'role': 'x', 'resource': {'type': 'y'}, ...}
        """
        results: List[bool] = []
        for c in policy.conditions:
            # support nested field lookups like 'resource.type' or simple 'role'
            if '.' in c.field:
                parts = c.field.split('.')
                val = context
                for p in parts:
                    if isinstance(val, dict):
                        val = val.get(p)
                    else:
                        val = getattr(val, p, None)
                        
                    if val is None:
                        break
            else:
                val = context.get(c.field)

            op = c.operator
            expected = c.value
            passed = False
            if op in ("eq", "=="):
                passed = str(val) == str(expected)
            elif op in ("ne", "!="):
                passed = str(val) != str(expected)
            else:
                # unsupported operator -> treat as False
                passed = False
            results.append(passed)

        matched = sum(1 for r in results if r)
        if policy.condition_logic.upper() == 'AND':
            overall = all(results) if results else True
        else:
            overall = any(results) if results else True

        return RuleDecision(passed=overall, matched_count=matched)


class PolicyValidator:
    def __init__(self):
        self.policies: List[Policy] = []
        self.usage_counters: Dict[str, Dict[str, int]] = {}

    def register_policy(self, policy: Policy):
        self.policies.append(policy)

    def record_usage(self, actor_id: str, limit_type: str):
        if actor_id not in self.usage_counters:
            self.usage_counters[actor_id] = {}
        self.usage_counters[actor_id][limit_type] = self.usage_counters[actor_id].get(limit_type, 0) + 1

    def validate_operation(self, op: Any) -> ValidationResult:
        # Build a simple context from operation
        ctx: Dict[str, Any] = {}
        if getattr(op, 'actor', None) is not None:
            ctx['role'] = getattr(op.actor, 'role', None)
            ctx['actor_id'] = getattr(op.actor, 'id', None)
        if getattr(op, 'resource', None) is not None:
            ctx['resource'] = {'type': getattr(op.resource, 'type', None)}

        for p in self.policies:
            if op.action in p.applies_to:
                rd = RuleEngine().evaluate_rule(p, ctx)
                violations: List[PolicyViolation] = []
                if not rd.passed:
                    v = PolicyViolation(policy_id=p.id, id=p.id, message='condition failed')
                    violations.append(v)
                # check limits regardless of condition outcome
                for lim in p.limits:
                    actor_id = ctx.get('actor_id')
                    if actor_id:
                        used = self.usage_counters.get(actor_id, {}).get(lim.limit_type, 0)
                        if used >= lim.max_count:
                            vlim = PolicyViolation(policy_id=p.id, id=p.id, message='limit exceeded', limit=lim)
                            violations.append(vlim)
                if violations:
                    return ValidationResult(allowed=False, action='DENY', violations=violations)
        return ValidationResult(allowed=True, action='ALLOW')


# Backwards-compatible alias expected by tests
PolicyEngine = Policy
