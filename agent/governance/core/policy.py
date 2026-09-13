"""
Governance Framework - Policy Module (compat shim + PoC)
Provides minimal PolicyCondition/PolicyLimit/PolicyValidator/PolicyViolation
and a simple Policy class for tests and imports.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agent.core.types import Operation

@dataclass
class PolicyCondition:
    # Support both old and new field names: tests may pass 'field'/'operator' or 'key'/'op'
    key: Optional[str] = None
    op: Optional[str] = None
    value: Any = None
    # aliases that tests may use
    field: Optional[str] = None
    operator: Optional[str] = None

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
    # support test-driven fields: limit_type / max_count and legacy name/limit
    name: str = ''
    limit: int = 0
    limit_type: str = ''
    max_count: int = 0

    def __post_init__(self):
        # normalize aliases
        if not self.name and self.limit_type:
            self.name = self.limit_type
        if not self.limit and self.max_count:
            self.limit = self.max_count

@dataclass
class PolicyViolation:
    reason: str
    policy_id: str = ''
    limit: Optional[PolicyLimit] = None

@dataclass
class ValidationResult:
    allowed: bool
    action: str = 'ALLOW'
    violations: List[PolicyViolation] = field(default_factory=list)

class PolicyValidator:
    def __init__(self):
        self.policies: List[Policy] = []
        # usage counters for quota checks: {actor_id: {resource_name: used}}
        self.usage_counters: Dict[str, Dict[str, int]] = {}

    def register_policy(self, policy: 'Policy') -> None:
        self.policies.append(policy)

    def record_usage(self, actor_id: str, resource_name: str, amount: int = 1) -> None:
        self.usage_counters.setdefault(actor_id, {})
        self.usage_counters[actor_id][resource_name] = self.usage_counters[actor_id].get(resource_name, 0) + amount

    def validate_operation(self, op: Operation) -> ValidationResult:
        # check each registered policy that applies to the operation
        for pol in self.policies:
            applies = False
            if getattr(pol, 'applies_to', None):
                if op.action in pol.applies_to:
                    applies = True
            if not applies:
                continue
            # evaluate conditions: if any condition denies, return DENY with violation
            for cond in getattr(pol, 'conditions', []):
                k = cond.key
                oper = cond.op
                val = cond.value
                if k == 'role':
                    role_val = getattr(op.actor, 'role', None)
                    if oper in ('ne', '!=') and role_val == val:
                        return ValidationResult(False, 'DENY', [PolicyViolation(reason='condition_denied', policy_id=pol.id)])
                    if oper in ('eq', '==') and role_val != val:
                        return ValidationResult(False, 'DENY', [PolicyViolation(reason='condition_denied', policy_id=pol.id)])
            # check limits
            for lim in getattr(pol, 'limits', []):
                used = self.usage_counters.get(getattr(op.actor, 'id', ''), {}).get(lim.name, 0)
                if used >= lim.limit:
                    return ValidationResult(False, 'DENY', [PolicyViolation(reason='limit_exceeded', policy_id=pol.id, limit=lim)])
            # if no denying condition or limit found, allow
            return ValidationResult(True, 'ALLOW', [])
        # default deny when no policy allows
        return ValidationResult(False, 'DENY', [])

class RuleEngine:
    def decide(self, input_data: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(True, 'ALLOW', [])

    def evaluate_rule(self, policy: 'Policy', context: Dict[str, Any]) -> ValidationResult:
        # Very small evaluator: check conditions in policy against context dict
        results = []
        for cond in getattr(policy, 'conditions', []):
            key = cond.key
            val = cond.value
            op = cond.op
            # support dot-path like 'resource.type'
            parts = key.split('.') if key else []
            cur = context
            for p in parts:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    cur = None
                    break
            if op in ('eq', '=='):
                results.append(cur == val)
            elif op in ('ne', '!='):
                results.append(cur != val)
            else:
                results.append(False)
        if getattr(policy, 'condition_logic', 'OR') == 'AND':
            allow = all(results) if results else True
        else:
            allow = any(results) if results else True
        # return a small object with .passed for legacy tests
        return type('R', (), {'passed': allow, 'action': 'ALLOW' if allow else 'DENY'})()

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
