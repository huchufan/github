"""
治理框架 (Governance Framework)

Hermes 系统的规则和约束层：访问控制、审计追踪、合规检查、约束管理、监控告警。

设计文档: 01_治理框架设计.md
"""

# Governance core public surface - lightweight exports for PoC
# Export only implemented PoC symbols to avoid import-time failures in tests.
from agent.governance.core.rbac import RBACManager, Role, Permission
from agent.governance.core.audit import AuditLog, AuditRecord
from agent.governance.core.policy import PolicyEngine, PolicyRule, Decision

__all__ = [
    # RBAC
    "RBACManager",
    "Role",
    "Permission",
    # Audit
    "AuditLog",
    "AuditRecord",
    # Policy
    "PolicyEngine",
    "PolicyRule",
    "Decision",
]
