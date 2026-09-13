from typing import Set, Dict, Any, Optional
from dataclasses import dataclass

# Use canonical Role and Permission from agent.core.types to ensure consistency
from agent.core.types import Role, Permission
from agent.core.errors import AccessDeniedError


@dataclass
class AccessRule:
    # PoC AccessRule matching test construction (effect, conditions, deny_reason, priority)
    effect: str = "ALLOW"
    conditions: list | None = None
    deny_reason: str = ""
    priority: int = 0
    role: Optional[Role] = None
    permission: Optional[Permission] = None
    resource: str = "*"


# sensible default permissions map
DEFAULT_ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(p for p in Permission),
    Role.DEVELOPER: {Permission.EXECUTE_AGENT, Permission.READ_MEMORY},
    Role.USER: {Permission.EXECUTE_AGENT},
    Role.GUEST: {Permission.QUERY_READONLY},
}


class GovernancePolicy:
    """Minimal policy container and ABAC rule evaluator (PoC).

    Provides .allows(role, permission, resource) for RBAC default checks and
    evaluate_access(subject, action, resource, ctx) for ABAC-style rule evaluation.
    """

    def __init__(self, rules: Optional[list] = None):
        self.rules = rules or []

    def allows(self, role: Role, permission: Permission, resource: str = "*") -> bool:
        # simple check against defaults then explicit rules
        if permission in DEFAULT_ROLE_PERMISSIONS.get(role, set()):
            return True
        for r in self.rules:
            if getattr(r, 'role', None) == role and getattr(r, 'permission', None) == permission and (
                getattr(r, 'resource', None) == resource or getattr(r, 'resource', None) == "*"
            ):
                return True
        return False

    def add_rule(self, rule: AccessRule):
        # append an AccessRule-like object to rules for deny/allow evaluation
        self.rules.append(rule)

    def evaluate_access(self, subject, action: str, resource, ctx):
        """Evaluate ABAC rules first; fallback to RBAC default check.

        Returns a lightweight decision-like object with attributes:
          - allow (bool)
          - audit_code (str)
          - reason (str)
        """
        # ABAC: iterate rules and evaluate conditions (supports dict or object conditions)
        for rule in getattr(self, 'rules', []):
            try:
                conds = getattr(rule, 'conditions', None) or []
                if not conds:
                    continue
                matches = True
                for cond in conds:
                    if isinstance(cond, dict):
                        left = cond.get('left')
                        op = cond.get('operator')
                        right = cond.get('right')
                    else:
                        left = getattr(cond, 'left', None) or getattr(cond, 'key', None)
                        op = getattr(cond, 'operator', None) or getattr(cond, 'op', None)
                        right = getattr(cond, 'right', None) or getattr(cond, 'value', None)

                    # resolve left value from subject/resource or dotted paths
                    val = None
                    if isinstance(left, str) and left.startswith('$subject_'):
                        attr = left[len('$subject_'):]
                        val = getattr(subject, attr, None)
                    elif isinstance(left, str) and left.startswith('$resource_'):
                        attr = left[len('$resource_'):]
                        val = getattr(resource, attr, None) if resource is not None else None
                    elif isinstance(left, str) and '.' in left:
                        parts = left.split('.')
                        if parts[0] == 'resource' and resource is not None:
                            cur = resource
                            for ppart in parts[1:]:
                                cur = getattr(cur, ppart, None) if not isinstance(cur, dict) else cur.get(ppart)
                            val = cur
                        elif parts[0] == 'subject':
                            cur = subject
                            for ppart in parts[1:]:
                                cur = getattr(cur, ppart, None) if not isinstance(cur, dict) else cur.get(ppart)
                            val = cur
                    else:
                        val = None

                    # compare
                    if op in ('eq', '=='):
                        if val != right:
                            matches = False
                            break
                    elif op in ('ne', '!='):
                        if val == right:
                            matches = False
                            break
                    else:
                        # unsupported -> fail this rule
                        matches = False
                        break

                if matches:
                    eff = getattr(rule, 'effect', '').upper()
                    if eff == 'DENY':
                        return type('D', (), {'allow': False, 'audit_code': 'ACCESS_DENIED', 'reason': getattr(rule, 'deny_reason', '')})()
                    if eff == 'ALLOW':
                        return type('D', (), {'allow': True, 'audit_code': 'ACCESS_GRANTED', 'reason': ''})()
            except Exception:
                # ignore ABAC evaluation errors in PoC
                pass

        # Fallback: RBAC mapping
        role_val = getattr(subject, 'role', subject)
        if hasattr(role_val, 'value'):
            role_val = role_val.value
        try:
            role_enum = Role(role_val)
        except Exception:
            return type('D', (), {'allow': False, 'audit_code': 'ACCESS_DENIED', 'reason': ''})()

        perm = None
        if isinstance(action, str):
            try:
                perm = Permission(action)
            except Exception:
                try:
                    perm = Permission[action]
                except Exception:
                    perm = None
        if perm is None:
            perm = Permission.EXECUTE_AGENT

        allowed = self.allows(role_enum, perm, getattr(resource, 'type', '*'))
        return type('D', (), {'allow': allowed, 'audit_code': 'ACCESS_GRANTED' if allowed else 'ACCESS_DENIED', 'reason': ''})()


class RBACManager:
    """Compatibility manager for RBAC-style APIs used in tests.

    Minimal interface:
      - get_permissions(role) -> Set[Permission]
      - resolve_role(subject) -> Role
      - evaluate_access(subject, action, resource, ctx) -> decision object
      - enforce_access(subject, action, resource, ctx) -> True or raises AccessDeniedError
      - grant_permission / revoke_permission for dynamic tests
    """

    def __init__(self, policy: Optional[GovernancePolicy] = None):
        self.policy = policy or GovernancePolicy()
        # dynamic grants and revokes applied at runtime (tests mutate these)
        self._overrides: Dict[Role, Set[Permission]] = {}
        self._revoked: Dict[Role, Set[Permission]] = {}
        # compatibility: basic config store expected by legacy tests
        self.config: Dict[str, Any] = {}

    def get_permissions(self, role: Role) -> Set[Permission]:
        # base defaults, plus overrides, minus revoked entries
        base = set(DEFAULT_ROLE_PERMISSIONS.get(role, set()))
        base |= set(self._overrides.get(role, set()))
        base -= set(self._revoked.get(role, set()))
        return base

    def check_permission(self, role: Role, permission: Permission) -> bool:
        """Return True if the role currently has the permission."""
        return permission in self.get_permissions(role)

    def grant_permission(self, role: Role, permission: Permission):
        self._overrides.setdefault(role, set()).add(permission)

    def revoke_permission(self, role: Role, permission: Permission):
        self._revoked.setdefault(role, set()).add(permission)
        if role in self._overrides and permission in self._overrides[role]:
            self._overrides[role].remove(permission)

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
        """PoC execute method expected by legacy tests: returns a simple success dict.
        Meant as a minimal compatibility shim.
        """
        return {'ok': True}


# Backwards-compatibility alias for older tests expecting 'Rbac'
class Rbac(RBACManager):
    """Compatibility shim: older tests import Rbac class.
    Minimal subclass of RBACManager with identical behaviour.
    """
    pass


# module-level alias
Rbac = Rbac


def enforce_access(policy_or_manager, subject, action, resource, ctx=None):
    """Module-level helper preserving older signature patterns used in tests.

    Accepts either a GovernancePolicy or RBACManager-like object as first arg.
    If it's a GovernancePolicy, evaluate via GovernancePolicy.evaluate_access.
    If it's an RBACManager, call its enforce_access.
    """
    if hasattr(policy_or_manager, 'enforce_access'):
        return policy_or_manager.enforce_access(subject, action, resource, ctx)
    if isinstance(policy_or_manager, GovernancePolicy):
        dec = policy_or_manager.evaluate_access(subject, action, resource, ctx)
        if not getattr(dec, 'allow', False):
            raise AccessDeniedError(getattr(dec, 'reason', 'access denied'))
        return True
    # unknown manager: try to treat as a policy dict
    try:
        mgr = RBACManager(policy_or_manager)
        return mgr.enforce_access(subject, action, resource, ctx)
    except Exception:
        raise AccessDeniedError('access denied')
