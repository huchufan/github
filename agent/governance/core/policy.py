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

class PolicyEngine:
    """Simple policy engine PoC: evaluate rules against a request context

    Policy evaluation algorithm (PoC):
    - iterate rules in order; first matching rule returns its effect
    - rule match: resource_type equals and action in actions and condition satisfied (if any)
    """

    def __init__(self, rules: Optional[List[PolicyRule]] = None):
        self.rules: List[PolicyRule] = rules or []

    def add_rule(self, rule: PolicyRule) -> None:
        self.rules.append(rule)

    def evaluate(self, resource_type: str, action: str, context: Optional[Dict[str, Any]] = None) -> Decision:
        ctx = context or {}
        for r in self.rules:
            if r.resource_type != resource_type:
                continue
            if action not in r.actions:
                continue
            if r.condition:
                if not self._match_condition(r.condition, ctx):
                    continue
            return r.effect
        return Decision.DENY

    def _match_condition(self, condition: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        # PoC: support simple equality checks in condition dict
        for k, v in condition.items():
            if ctx.get(k) != v:
                return False
        return True
