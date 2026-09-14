from typing import Set, Dict, Optional
# Use shared Role/Permission types from agent.core.types so tests import the same enums
from agent.core.types import Role, Permission

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# Compatibility decision object used by GovernancePolicy.evaluate_access
@dataclass
class PolicyDecision:
    allow: bool = False
    reason: str = ""
    audit_code: str = "ACCESS_DENIED"

@dataclass
class AccessRule:
    id: str = ""
    effect: str = "ALLOW"
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    deny_reason: Optional[str] = None
    priority: int = 0

DEFAULT_ROLE_PERMISSIONS = {
    'admin': [p.name for p in Permission],
    'developer': ['EXECUTE_AGENT', 'READ_MEMORY', 'QUERY_READONLY'],
    'user': ['EXECUTE_AGENT', 'QUERY_READONLY'],
    'guest': ['QUERY_READONLY'],
}

@dataclass
class GovernancePolicy:
    name: str = "default"
    rules: list = field(default_factory=list)

    def _resolve_value(self, token: str, subject: Any, resource: Any, ctx: Any):
        # token examples: "$subject_org", "$subject.organization", "$resource.type"
        if not token or not token.startswith("$"):
            return None
        key = token[1:]
        # support subject_foo or subject.foo
        if key.startswith("subject_"):
            attr = key[len("subject_"):]
            # common alias mapping (e.g. $subject_org -> subject.organization)
            alias_map = {
                'org': 'organization',
                'org_id': 'organization',
            }
            mapped = alias_map.get(attr, attr)
            if hasattr(subject, mapped):
                return getattr(subject, mapped, None)
            # fallback: try raw attr
            return getattr(subject, attr, None)
        if key.startswith("subject."):
            attr = key.split('.', 1)[1]
            return getattr(subject, attr, None)
        if key.startswith("resource_"):
            attr = key[len("resource_"):]
            alias_map = {'id': 'id', 'owner': 'owner'}
            mapped = alias_map.get(attr, attr)
            if hasattr(resource, mapped):
                return getattr(resource, mapped, None)
            return getattr(resource, attr, None)
        if key.startswith("resource."):
            attr = key.split('.', 1)[1]
            return getattr(resource, attr, None)
        if key.startswith("ctx_"):
            attr = key[len("ctx_"):]
            return getattr(ctx, attr, None)
        if key.startswith("ctx."):
            attr = key.split('.', 1)[1]
            return getattr(ctx, attr, None)
        return None

    def _eval_condition(self, cond: Dict[str, Any], subject: Any, resource: Any, ctx: Any) -> bool:
        left = cond.get("left")
        op = cond.get("operator")
        right = cond.get("right")
        lval = self._resolve_value(left, subject, resource, ctx) if isinstance(left, str) and left.startswith("$") else left
        rval = right
        if op in ("eq", "=="):
            return str(lval) == str(rval)
        if op in ("ne", "!="):
            return str(lval) != str(rval)
        # extend as needed
        return False

    def evaluate_access(self, subject: Any, action: str, resource: Any, ctx: Any) -> Any:
        """Evaluate ABAC-like governance policy (PoC).

        Behavior (PoC):
        - iterate rules ordered by priority desc; first matching rule returns its effect
        - support simple condition objects with left (token), operator, right
        - return a Decision object with allow/reason/audit_code to satisfy tests
        """
        # default deny decision
        decision = PolicyDecision(allow=False, reason="Default deny", audit_code="ACCESS_DENIED")

        # sort by priority descending
        rules = sorted(self.rules, key=lambda r: getattr(r, "priority", 0), reverse=True)
        for rule in rules:
            # if no conditions, rule matches all
            conds = getattr(rule, "conditions", []) or []
            matched = True
            for c in conds:
                if not self._eval_condition(c, subject, resource, ctx):
                    matched = False
                    break
            if matched:
                if getattr(rule, "effect", "ALLOW").upper() == "DENY":
                    decision.allow = False
                    decision.reason = getattr(rule, "deny_reason", "") or "Access denied by policy"
                    decision.audit_code = getattr(rule, "audit_code", "ACCESS_DENIED_RBAC")
                    return decision
                else:
                    decision.allow = True
                    decision.reason = getattr(rule, "deny_reason", "") or "Allowed by policy"
                    decision.audit_code = getattr(rule, "audit_code", "ACCESS_ALLOWED")
                    return decision
        return decision

    def add_rule(self, rule: Any) -> None:
        self.rules.append(rule)


from agent.core.errors import AccessDeniedError

def enforce_access(policy: GovernancePolicy, subject: Any, action: str, resource: Any, ctx: Any):
    """Evaluate policy and raise AccessDeniedError when denied (PoC).
    Expected to be used in tests with pytest.raises(AccessDeniedError).
    """
    try:
        decision = policy.evaluate_access(subject, action, resource, ctx)
    except Exception:
        # On unexpected errors, deny
        raise AccessDeniedError("policy evaluation failed")

    allow = getattr(decision, 'allow', False)
    if not allow:
        reason = getattr(decision, 'reason', 'Access denied')
        raise AccessDeniedError(reason)
    return True


class RBACManager:
    """角色基础访问控制管理"""

    def __init__(self):
        # Initialize roles from DEFAULT_ROLE_PERMISSIONS, normalize to sets of Permission
        self.roles: Dict[Role, Set[Permission]] = {}
        for role_name, perms in DEFAULT_ROLE_PERMISSIONS.items():
            try:
                role_enum = Role(role_name)
            except Exception:
                continue
            if isinstance(perms, list):
                normalized = set()
                for p in perms:
                    if p in Permission.__members__:
                        normalized.add(Permission[p])
                self.roles[role_enum] = normalized
            else:
                self.roles[role_enum] = set(perms) if isinstance(perms, set) else set()

    def check_permission(self, role: Role, permission: Permission) -> bool:
        """检查权限"""
        if role not in self.roles:
            return False
        return permission in self.roles.get(role, set())

    def grant_permission(self, role: Role, permission: Permission):
        """授予权限"""
        if role not in self.roles:
            self.roles[role] = set()
        self.roles[role].add(permission)

    def revoke_permission(self, role: Role, permission: Permission):
        """撤销权限"""
        if role in self.roles:
            self.roles[role].discard(permission)

    def get_permissions(self, role: Role) -> Set[Permission]:
        return self.roles.get(role, set())

    def resolve_role(self, role_name: str) -> Role:
        try:
            return Role(role_name)
        except Exception:
            return Role.GUEST
