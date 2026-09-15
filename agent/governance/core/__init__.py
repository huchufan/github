"""
治理框架 (Governance Framework)

Hermes 系统的规则和约束层：访问控制、审计追踪、合规检查、约束管理、监控告警。

设计文档: 01_治理框架设计.md
"""

from agent.governance.core.rbac import (
    AccessRule,
    DEFAULT_ROLE_PERMISSIONS,
    GovernancePolicy,
    RBACManager,
    enforce_access,
)
from agent.governance.core.audit import AuditLogger, AuditAnalyzer, ComplianceReport, AnomalyReport
from agent.governance.core.policy import (
    Policy,
    PolicyCondition,
    PolicyLimit,
    PolicyValidator,
    PolicyViolation,
    RuleEngine,
    RuleDecision,
    ValidationResult,
)
from agent.governance.core.constraints import (
    ConstraintViolation,
    ConstraintCheckResult,
    ExecutionConstraints,
    ResourceQuotaManager,
)
from agent.governance.core.monitor import GovernanceMonitor, GovernanceAlert
from agent.governance.core.rules import BehaviorRule, BehaviorRuleStore

__all__ = [
    # RBAC / ABAC
    "AccessRule",
    "DEFAULT_ROLE_PERMISSIONS",
    "GovernancePolicy",
    "RBACManager",
    "enforce_access",
    # 审计
    "AuditLogger",
    "AuditAnalyzer",
    "ComplianceReport",
    "AnomalyReport",
    # 策略
    "Policy",
    "PolicyCondition",
    "PolicyLimit",
    "PolicyValidator",
    "PolicyViolation",
    "RuleEngine",
    "RuleDecision",
    "ValidationResult",
    # 约束
    "ConstraintViolation",
    "ConstraintCheckResult",
    "ExecutionConstraints",
    "ResourceQuotaManager",
    # 监控
    "GovernanceMonitor",
    "GovernanceAlert",
    # 行为规则
    "BehaviorRule",
    "BehaviorRuleStore",
]
