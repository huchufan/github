"""
治理框架 - RBAC + ABAC 访问控制模块 (Access Control)

角色基础访问控制 (RBAC) 与属性化访问控制 (ABAC) 决策引擎。

设计文档: 01_治理框架设计.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from agent.core.types import (
    AccessDecision,
    Actor,
    ExecutionContext,
    Permission,
    Resource,
    Role,
)
from agent.core.errors import AccessDeniedError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RBAC 角色权限默认表
# ---------------------------------------------------------------------------

DEFAULT_ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),
    Role.DEVELOPER: {
        Permission.EXECUTE_AGENT,
        Permission.READ_MEMORY,
        Permission.SKILL_CREATE,
        Permission.SKILL_EXECUTE,
        Permission.READ_CONFIG,
        Permission.AUDIT_READ_OWN,
    },
    Role.USER: {Permission.EXECUTE_AGENT, Permission.READ_MEMORY, Permission.SKILL_EXECUTE},
    Role.SERVICE: {Permission.EXECUTE_SCHEDULED, Permission.SKILL_EXECUTE, Permission.GATEWAY_WRITE},
    Role.GUEST: {Permission.QUERY_READONLY, Permission.SKILL_EXPLORE},
}


class RBACManager:
    """
    角色基础访问控制管理器。

    维护角色到权限集合的映射，支持权限检查、授予与撤销。
    """

    def __init__(self, role_permissions: Optional[Dict[Role, Set[Permission]]] = None):
        self.roles: Dict[Role, Set[Permission]] = {
            role: set(perms) for role, perms in (role_permissions or DEFAULT_ROLE_PERMISSIONS).items()
        }

    def check_permission(self, role: Role, permission: Permission) -> bool:
        """检查某角色是否拥有某权限。"""
        return permission in self.roles.get(role, set())

    def grant_permission(self, role: Role, permission: Permission) -> None:
        """授予权限。"""
        self.roles.setdefault(role, set()).add(permission)
        logger.info("Granted %s to role %s", permission.value, role.value)

    def revoke_permission(self, role: Role, permission: Permission) -> None:
        """撤销权限。"""
        self.roles.get(role, set()).discard(permission)
        logger.info("Revoked %s from role %s", permission.value, role.value)

    def get_permissions(self, role: Role) -> Set[Permission]:
        """获取角色权限集合。"""
        return set(self.roles.get(role, set()))

    def resolve_role(self, role_name: str) -> Role:
        """将字符串角色名解析为 Role 枚举（找不到时回退到 GUEST）。"""
        try:
            return Role(role_name)
        except ValueError:
            return Role.GUEST


# ---------------------------------------------------------------------------
# ABAC 属性化访问控制
# ---------------------------------------------------------------------------

@dataclass
class AccessRule:
    """一条属性化访问规则。"""
    effect: str = "DENY"  # ALLOW / DENY
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    deny_reason: str = "Rule matched"
    priority: int = 0


class GovernancePolicy:
    """
    属性化访问控制决策引擎。

    基于 Subject / Resource / Action / Context 四维属性评估访问决策，
    遵循「默认拒绝」原则。
    """

    def __init__(self):
        self.rules: List[AccessRule] = []
        self.rbac = RBACManager()

    def add_rule(self, rule: AccessRule) -> None:
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    # -- 条件评估 -----------------------------------------------------------

    def matches_all_conditions(self, conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        for cond in conditions:
            if not self._evaluate_condition(cond, context):
                return False
        return True

    def _evaluate_condition(self, cond: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        op = cond.get("operator", "eq")
        left = self._resolve(cond.get("left"), ctx)
        right = self._resolve(cond.get("right"), ctx)

        if op == "eq":
            return left == right
        if op == "ne":
            return left != right
        if op == "gt":
            return left > right
        if op == "gte":
            return left >= right
        if op == "lt":
            return left < right
        if op == "lte":
            return left <= right
        if op == "in":
            return left in right
        if op == "not_in":
            return left not in right
        if op == "contains":
            return left in right
        raise ValueError(f"Unknown condition operator: {op}")

    @staticmethod
    def _resolve(path: Any, ctx: Dict[str, Any]) -> Any:
        if not isinstance(path, str) or not path.startswith("$"):
            return path
        keys = path.lstrip("$").split(".")
        value: Any = ctx
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = getattr(value, key, None)
        return value

    # -- 主决策 -------------------------------------------------------------

    def evaluate_access(
        self,
        subject: Actor,
        action: str,
        resource: Resource,
        context: ExecutionContext,
    ) -> AccessDecision:
        """
        基于属性决定访问权限。

        属性维度：
        - Subject: role, permissions, clearance_level, organization
        - Resource: type, sensitivity, owner, tags
        - Action: operation_type, risk_level, required_approvals
        - Context: time, location, network, threat_level
        """
        ctx = {
            "subject": subject,
            "subject_id": subject.id,
            "subject_role": subject.role,
            "subject_clearance": subject.clearance_level,
            "subject_org": subject.organization,
            "resource": resource,
            "resource_type": resource.type,
            "resource_owner": resource.owner,
            "resource_sensitivity": resource.sensitivity,
            "resource_classification": resource.classification,
            "action": action,
            "context": context,
            "threat_level": context.threat_level,
        }

        # 先检查 RBAC：action 映射为权限进行粗粒度判定
        permission = self._action_to_permission(action)
        role = self.rbac.resolve_role(subject.role)
        if permission is not None and not self.rbac.check_permission(role, permission):
            return AccessDecision(
                allow=False,
                reason=f"Role '{subject.role}' lacks permission '{permission.value}'",
                audit_code="ACCESS_DENIED_RBAC",
            )

        # 再逐条评估 ABAC 规则（DENY 优先）
        for rule in self.rules:
            if self.matches_all_conditions(rule.conditions, ctx):
                if rule.effect == "DENY":
                    return AccessDecision(
                        allow=False,
                        reason=rule.deny_reason,
                        audit_code="ACCESS_DENIED_ABAC",
                    )

        # 默认拒绝原则
        return AccessDecision(allow=False, reason="Default deny", audit_code="ACCESS_DENIED")

    @staticmethod
    def _action_to_permission(action: str) -> Optional[Permission]:
        """将动作字符串映射为权限（用于 RBAC 粗粒度检查）。"""
        mapping = {
            "agent:execute": Permission.EXECUTE_AGENT,
            "agent:execute_own": Permission.EXECUTE_OWN,
            "agent:execute_scheduled": Permission.EXECUTE_SCHEDULED,
            "memory:read": Permission.READ_MEMORY,
            "config:write": Permission.WRITE_CONFIG,
            "config:read": Permission.READ_CONFIG,
            "config:modify_system": Permission.MODIFY_SYSTEM,
            "audit:read": Permission.AUDIT_LOG,
            "skill:create": Permission.SKILL_CREATE,
            "skill:execute": Permission.SKILL_EXECUTE,
            "skill:explore": Permission.SKILL_EXPLORE,
            "policy:manage": Permission.POLICY_MANAGE,
            "gateway:write": Permission.GATEWAY_WRITE,
            "agent:query_readonly": Permission.QUERY_READONLY,
            "data:export": Permission.DATA_EXPORT,
        }
        return mapping.get(action)


def enforce_access(
    policy: GovernancePolicy,
    subject: Actor,
    action: str,
    resource: Resource,
    context: ExecutionContext,
) -> AccessDecision:
    """执行访问控制并抛出异常（供编排/自动化层调用）。"""
    decision = policy.evaluate_access(subject, action, resource, context)
    if not decision.allow:
        raise AccessDeniedError(decision.reason)
    return decision


__all__ = [
    "AccessRule",
    "GovernancePolicy",
    "RBACManager",
    "DEFAULT_ROLE_PERMISSIONS",
    "enforce_access",
]
