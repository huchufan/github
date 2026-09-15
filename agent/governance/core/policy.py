"""
治理框架 - 合规检查层 (Compliance & Policy)

策略验证引擎与决策规则执行引擎。

设计文档: 01_治理框架设计.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.core.types import Decision, Operation, Severity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class PolicyCondition:
    """策略条件。"""
    field: str = ""
    operator: str = "eq"  # eq/ne/gt/gte/lt/lte/in/contains
    value: Any = None
    description: str = ""


@dataclass
class PolicyLimit:
    """策略配额/限制。"""
    limit_type: str = ""
    max_count: int = 0
    window: str = "24h"


@dataclass
class Policy:
    """一条策略规则。"""
    id: str = ""
    name: str = ""
    applies_to: List[str] = field(default_factory=list)
    conditions: List[PolicyCondition] = field(default_factory=list)
    limits: List[PolicyLimit] = field(default_factory=list)
    violation_severity: str = Severity.MEDIUM.value
    suggested_action: str = ""
    condition_logic: str = "AND"


@dataclass
class PolicyViolation:
    """策略违规。"""
    policy_id: str = ""
    severity: str = Severity.MEDIUM.value
    description: str = ""
    condition: Optional[PolicyCondition] = None
    limit: Optional[PolicyLimit] = None
    suggested_action: str = ""


@dataclass
class ValidationResult:
    """策略验证结果。"""
    action: str = Decision.ALLOW.value
    violations: List[PolicyViolation] = field(default_factory=list)
    warning_count: int = 0

    @property
    def allowed(self) -> bool:
        return self.action != Decision.DENY.value


@dataclass
class RuleDecision:
    """规则决策结果。"""
    rule_id: str = ""
    passed: bool = False
    reason: str = ""
    failed_condition: Optional[PolicyCondition] = None


# ---------------------------------------------------------------------------
# 条件评估工具
# ---------------------------------------------------------------------------

def _evaluate(field_value: Any, operator: str, expected: Any) -> bool:
    if operator == "eq":
        return field_value == expected
    if operator == "ne":
        return field_value != expected
    if operator == "gt":
        return field_value > expected
    if operator == "gte":
        return field_value >= expected
    if operator == "lt":
        return field_value < expected
    if operator == "lte":
        return field_value <= expected
    if operator == "in":
        return field_value in expected
    if operator == "contains":
        return expected in field_value
    raise ValueError(f"Unknown operator: {operator}")


def _resolve_field(obj: Any, path: str) -> Any:
    value: Any = obj
    for key in path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        else:
            value = getattr(value, key, None)
    return value


# ---------------------------------------------------------------------------
# 规则引擎
# ---------------------------------------------------------------------------

class RuleEngine:
    """决策规则执行引擎。"""

    def evaluate_rule(self, rule: Policy, context: Dict[str, Any]) -> RuleDecision:
        """评估规则是否满足。"""
        decisions: List[bool] = []
        failed: Optional[PolicyCondition] = None

        for condition in rule.conditions:
            field_value = _resolve_field(context, condition.field)
            passed = _evaluate(field_value, condition.operator, condition.value)
            decisions.append(passed)
            if not passed and failed is None:
                failed = condition
            # AND 逻辑可提前终止
            if rule.condition_logic == "AND" and not passed:
                return RuleDecision(
                    rule_id=rule.id,
                    passed=False,
                    reason=f"Condition '{condition.field}' failed",
                    failed_condition=condition,
                )

        if rule.condition_logic == "AND":
            overall = all(decisions)
        elif rule.condition_logic == "OR":
            overall = any(decisions)
        else:
            overall = all(decisions)

        return RuleDecision(
            rule_id=rule.id,
            passed=overall,
            reason="" if overall else "Conditions not met",
            failed_condition=failed,
        )


# ---------------------------------------------------------------------------
# 策略验证引擎
# ---------------------------------------------------------------------------

class PolicyValidator:
    """实时策略验证和合规检查。"""

    def __init__(self, rule_engine: Optional[RuleEngine] = None):
        self.rule_engine = rule_engine or RuleEngine()
        self.policies: List[Policy] = []
        self.usage_counters: Dict[str, Dict[str, int]] = {}

    def register_policy(self, policy: Policy) -> None:
        self.policies.append(policy)

    def validate_operation(self, operation: Operation, policies: Optional[List[Policy]] = None) -> ValidationResult:
        """验证操作是否符合策略。"""
        target = policies if policies is not None else self.policies
        violations: List[PolicyViolation] = []

        context = {
            "action": operation.action,
            "actor": operation.actor,
            "resource": operation.resource,
            "context": operation.context,
        }
        if operation.actor is not None:
            context.update({
                "role": operation.actor.role,
                "subject_id": operation.actor.id,
                "clearance_level": operation.actor.clearance_level,
            })
        if operation.resource is not None:
            context.update({
                "resource_owner": operation.resource.owner,
                "resource_classification": operation.resource.classification,
                "resource_type": operation.resource.type,
            })

        for policy in target:
            # 1. 检查是否适用
            if not policy.applies_to or operation.action not in policy.applies_to:
                continue

            # 2. 检查所有条件
            decision = self.rule_engine.evaluate_rule(policy, context)
            if not decision.passed:
                violations.append(
                    PolicyViolation(
                        policy_id=policy.id,
                        severity=policy.violation_severity,
                        description=decision.reason,
                        condition=decision.failed_condition,
                        suggested_action=policy.suggested_action,
                    )
                )

            # 3. 检查配额和限制
            for limit in policy.limits:
                if self.exceeds_limit(limit, operation):
                    violations.append(
                        PolicyViolation(
                            policy_id=policy.id,
                            severity=Severity.HIGH.value,
                            description=f"Limit '{limit.limit_type}' exceeded ({limit.max_count})",
                            limit=limit,
                        )
                    )

        # 4. 决定是否允许
        action = self._determine_action(violations)

        return ValidationResult(
            action=action,
            violations=violations,
            warning_count=len([v for v in violations if v.severity == Severity.INFO.value]),
        )

    def exceeds_limit(self, limit: PolicyLimit, operation: Operation) -> bool:
        """检查是否超过限制（基于运行中计数）。"""
        if operation.actor is None:
            return False
        key = f"{limit.limit_type}"
        counter = self.usage_counters.setdefault(operation.actor.id, {})
        return counter.get(key, 0) >= limit.max_count

    def record_usage(self, actor_id: str, limit_type: str) -> None:
        """记录一次使用（供执行层在操作成功时调用）。"""
        counter = self.usage_counters.setdefault(actor_id, {})
        counter[limit_type] = counter.get(limit_type, 0) + 1

    @staticmethod
    def _determine_action(violations: List[PolicyViolation]) -> str:
        if not violations:
            return Decision.ALLOW.value
        severity_levels = {v.severity for v in violations}
        if Severity.CRITICAL.value in severity_levels:
            return Decision.DENY.value
        if Severity.HIGH.value in severity_levels:
            return Decision.REQUIRE_APPROVAL.value
        return Decision.WARN.value


__all__ = [
    "Policy",
    "PolicyCondition",
    "PolicyLimit",
    "PolicyViolation",
    "PolicyValidator",
    "RuleEngine",
    "RuleDecision",
    "ValidationResult",
]
