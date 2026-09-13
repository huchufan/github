from typing import Set, Dict, Any, Optional
from dataclasses import dataclass

# canonical Role/Permission from core types
from agent.core.types import Role, Permission, Actor, Resource, ExecutionContext
from agent.core.errors import AccessDeniedError


@dataclass
class AccessRule:
    """PoC AccessRule shape used by tests.

    Fields: effect ('ALLOW'|'DENY'), conditions (list of dicts), deny_reason, priority,
    optional role/permission/resource for RBAC-bound rules.
    """
    effect: str = "ALLOW"
    conditions: Optional[list] = None
    deny_reason: str = ""
    priority: int = 0
    role: Optional[Role] = None
    permission: Optional[Permission] = None
    resource: str = "*"


# sensible default RBAC mapping used by tests
DEFAULT_ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(p for p in Permission),
    Role.DEVELOPER: {Permission.EXECUTE_AGENT, Permission.READ_MEMORY},
    Role.USER: {Permission.EXECUTE_AGENT},
    Role.GUEST: {Permission.QUERY_READONLY},
}


class GovernancePolicy:
    """Minimal policy container and ABAC rule evaluator (PoC).

    Methods:
      - add_rule(rule)
      - evaluate_access(subject, action, resource, ctx) -> decision object
    """

    def __init__(self, rules: Optional[list] = None):
        self.rules = rules or []

    def add_rule(self, rule: AccessRule):
        self.rules.append(rule)

    def _eval_condition(self, cond, subject, resource):
        # cond is expected as dict {left, operator, right}
        left = cond.get('left')
        op = cond.get('operator')
        right = cond.get('right')
        # handle $subject_token and $resource_token
        if isinstance(left, str) and left.startswith('$subject_'):
            token = left[len('$subject_'):]
            val = getattr(subject, token, None) if subject is not None else None
            if val is None and hasattr(subject, 'organization') and 'org' in token.lower():
                val = getattr(subject, 'organization', None)
        elif isinstance(left, str) and left.startswith('$resource_'):
            token = left[len('$resource_'):]
            val = getattr(resource, token, None) if resource is not None else None
        else:
            val = None
            if isinstance(left, str) and '.' in left:
                parts = left.split('.')
                cur = subject if parts[0] == 'subject' else resource if parts[0] == 'resource' else None
                for p in parts[1:]:
                    if cur is None:
                        break
                    cur = getattr(cur, p, None) if not isinstance(cur, dict) else cur.get(p)
                val = cur
        if op in ('eq', '=='):
            return val == right
        if op in ('ne', '!='):
            return val != right
        return False

    def evaluate_access(self, subject, action: str, resource, ctx: Optional[ExecutionContext] = None):
        # ABAC rules
        for rule in getattr(self, 'rules', []):
            conds = rule.conditions or []
            if not conds:
                continue
            passed = True
            for cond in conds:
                try:
                    if not self._eval_condition(cond, subject, resource):
                        passed = False
                        break
                except Exception:
                    passed = False
                    break
            if passed:
                eff = (rule.effect or "").upper()
                if eff == 'DENY':
                    return type('D', (), {'allow': False, 'audit_code': 'ACCESS_DENIED', 'reason': getattr(rule, 'deny_reason', '')})()
                if eff == 'ALLOW':
                    return type('D', (), {'allow': True, 'audit_code': 'ACCESS_GRANTED', 'reason': ''})()
        # RBAC fallback
        perm = None
        try:
            perm = Permission(action)
        except Exception:
            try:
                perm = Permission[action]
            except Exception:
                perm = None
        role_val = getattr(subject, 'role', subject)
        try:
            role_enum = Role(role_val) if not isinstance(role_val, Role) else role_val
        except Exception:
            role_enum = Role.GUEST
        allowed = False
        if perm is not None:
            allowed = perm in DEFAULT_ROLE_PERMISSIONS.get(role_enum, set())
        return type('D', (), {'allow': bool(allowed), 'audit_code': 'ACCESS_GRANTED' if allowed else 'ACCESS_DENIED_RBAC', 'reason': ''})()


class RBACManager:
    """Compatibility manager providing RBAC-style helpers expected by tests."""

    def __init__(self, policy: Optional[GovernancePolicy] = None):
        self.policy = policy or GovernancePolicy()
        self._overrides: Dict[Role, Set[Permission]] = {}
        self._revoked: Dict[Role, Set[Permission]] = {}
        self.config: Dict[str, Any] = {}

    def get_permissions(self, role: Role) -> Set[Permission]:
        if not isinstance(role, Role):
            try:
                role = Role(role)
            except Exception:
                return set()
        if role == Role.ADMIN:
            return set(p for p in Permission)
        base = set(DEFAULT_ROLE_PERMISSIONS.get(role, set()))
        base |= set(self._overrides.get(role, set()))
        base -= set(self._revoked.get(role, set()))
        return base

    def check_permission(self, role: Role, permission: Permission) -> bool:
        # normalize
        try:
            if not isinstance(role, Role):
                role = Role(role)
        except Exception:
            pass
        try:
            if not isinstance(permission, Permission):
                permission = Permission(permission)
        except Exception:
            pass
        # revoked takes precedence
        if role in self._revoked and permission in self._revoked.get(role, set()):
            return False
        # overrides
        if role in self._overrides and permission in self._overrides.get(role, set()):
            return True
        # admin implicit
        if role == Role.ADMIN:
            return True
        return permission in self.get_permissions(role)

    def grant_permission(self, role: Role, permission: Permission):
        try:
            if not isinstance(role, Role):
                role = Role(role)
        except Exception:
            pass
        try:
            if not isinstance(permission, Permission):
                permission = Permission(permission)
        except Exception:
            pass
        if role in self._revoked and permission in self._revoked.get(role, set()):
            try:
                self._revoked[role].remove(permission)
            except Exception:
                pass
        self._overrides.setdefault(role, set()).add(permission)

    def revoke_permission(self, role: Role, permission: Permission):
        try:
            if not isinstance(role, Role):
                role = Role(role)
        except Exception:
            pass
        try:
            if not isinstance(permission, Permission):
                permission = Permission(permission)
        except Exception:
            pass
        self._revoked.setdefault(role, set()).add(permission)
        if role in self._overrides and permission in self._overrides[role]:
            try:
                self._overrides[role].remove(permission)
            except Exception:
                pass

    def resolve_role(self, subject) -> Role:
        rv = getattr(subject, 'role', None)
        if rv is None:
            return Role.GUEST
        try:
            return Role(rv) if not isinstance(rv, Role) else rv
        except Exception:
            return Role.GUEST

    def evaluate_access(self, subject, action: str, resource, ctx=None):
        return self.policy.evaluate_access(subject, action, resource, ctx)

    def enforce_access(self, subject, action: str, resource, ctx=None):
        dec = self.evaluate_access(subject, action, resource, ctx)
        if not getattr(dec, 'allow', False):
            raise AccessDeniedError(getattr(dec, 'reason', 'access denied'))
        return True

    def execute(self, *args, **kwargs):
        return {'ok': True}


# legacy alias
class Rbac(RBACManager):
    pass

Rbac = Rbac


def enforce_access(policy_or_manager, subject, action, resource, ctx=None):
    if hasattr(policy_or_manager, 'enforce_access'):
        return policy_or_manager.enforce_access(subject, action, resource, ctx)
    if isinstance(policy_or_manager, GovernancePolicy):
        dec = policy_or_manager.evaluate_access(subject, action, resource, ctx)
        if not getattr(dec, 'allow', False):
            raise AccessDeniedError(getattr(dec, 'reason', 'access denied'))
        return True
    try:
        mgr = RBACManager(policy_or_manager)
        return mgr.enforce_access(subject, action, resource, ctx)
    except Exception:
        raise AccessDeniedError('access denied')
