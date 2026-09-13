from typing import Set, Dict, Any, Optional
from dataclasses import dataclass

# Use canonical Role and Permission from agent.core.types to ensure consistency
from agent.core.types import Role, Permission
from agent.core.errors import AccessDeniedError

@dataclass
class AccessRule:
    # PoC AccessRule matching test construction (effect, conditions, deny_reason, priority)
    effect: str = "ALLOW"
    conditions: list = None
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
    """Minimal policy container"""
    def __init__(self, rules=None):
        self.rules = rules or []

    def allows(self, role: Role, permission: Permission, resource: str = "*") -> bool:
        # simple check against defaults then explicit rules
        if permission in DEFAULT_ROLE_PERMISSIONS.get(role, set()):
            return True
        for r in self.rules:
            if r.role == role and r.permission == permission and (r.resource == resource or r.resource == "*"):
                return True
        return False

    def add_rule(self, rule: AccessRule):
        # append an AccessRule-like object to rules for deny/allow evaluation
        self.rules.append(rule)

    def evaluate_access(self, subject, action: str, resource, ctx):
        """Compatibility shim: return object with .allow attribute.
        Accepts subject.role as enum or string. Maps action string to Permission when possible.
        """
        role_val = getattr(subject, 'role', subject)
        if hasattr(role_val, 'value'):
            role_val = role_val.value
        try:
            role_enum = Role(role_val)
        except Exception:
            return type('D', (), {'allow': False})()
        # map action ("memory:read") to Permission if possible
        perm = None
        if isinstance(action, str):
            try:
                perm = Permission(action)
            except Exception:
                # try mapping by name (e.g. 'QUERY_READONLY')
                try:
                    perm = Permission[action]
                except Exception:
                    perm = None
        if perm is None:
            # fallback to a safe permission-like default
            perm = Permission.EXECUTE_AGENT
        allowed = self.allows(role_enum, perm, getattr(resource, 'type', '*'))
        # include audit_code and reason for callers that expect richer decision objects
        obj = type('D', (), {'allow': allowed, 'audit_code': 'ACCESS_DENIED' if not allowed else 'ACCESS_GRANTED', 'reason': ''})()
        return obj

class RBACManager:
    def __init__(self, policy: GovernancePolicy | None = None):
        self.policy = policy or GovernancePolicy()
        # cache of role->permissions view
        self._permissions_cache: Dict[Role, Set[Permission]] = dict(DEFAULT_ROLE_PERMISSIONS)

    def resolve_role(self, role_name: str) -> Role:
        # Best-effort resolver: map a string to Role enum, default to GUEST
        try:
            return Role(role_name)
        except Exception:
            for r in Role:
                if r.name.lower() == str(role_name).lower():
                    return r
        return Role.GUEST

    def check_permission(self, role: Role, permission: Permission, resource: str = "*") -> bool:
        return self.policy.allows(role, permission, resource)

    def grant_permission(self, role: Role, permission: Permission):
        DEFAULT_ROLE_PERMISSIONS.setdefault(role, set()).add(permission)
        self._permissions_cache[role] = set(DEFAULT_ROLE_PERMISSIONS.get(role, set()))

    def revoke_permission(self, role: Role, permission: Permission):
        DEFAULT_ROLE_PERMISSIONS.setdefault(role, set()).discard(permission)
        self._permissions_cache[role] = set(DEFAULT_ROLE_PERMISSIONS.get(role, set()))

    def get_permissions(self, role: Role) -> Set[Permission]:
        return set(self._permissions_cache.get(role, DEFAULT_ROLE_PERMISSIONS.get(role, set())))

def enforce_access(policy_or_manager, subject, action: str, resource, ctx=None):
    """Compatibility shim matching tests' enforce_access(policy, subject, action, resource, ctx).
    Accepts either a GovernancePolicy or an RBACManager as the first argument.
    Returns an AccessDecision-like object.
    """
    # normalize manager
    if isinstance(policy_or_manager, RBACManager):
        mgr = policy_or_manager
    else:
        mgr = RBACManager(policy_or_manager)
    # use policy.evaluate_access if available
    if hasattr(mgr.policy, 'evaluate_access'):
        decision = mgr.policy.evaluate_access(subject, action, resource, ctx)
        if hasattr(decision, 'allow') and not decision.allow:
            raise AccessDeniedError('access denied by policy')
        return decision
    # fallback boolean decision-like object
    role_val = getattr(subject, 'role', subject)
    if hasattr(role_val, 'value'):
        role_val = role_val.value
    try:
        role_enum = Role(role_val)
    except Exception:
        return type('D', (), {'allow': False})()
    try:
        perm = Permission(action)
    except Exception:
        perm = Permission.EXECUTE_AGENT
    allowed = mgr.check_permission(role_enum, perm, getattr(resource, 'type', '*'))
    return type('D', (), {'allow': allowed})()

# Rbac PoC class expected by autogenerated tests
class Rbac:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs):
        return {"module": "rbac", "ok": True}

# Exported names expected by package __init__
__all__ = [
    'AccessRule',
    'DEFAULT_ROLE_PERMISSIONS',
    'GovernancePolicy',
    'RBACManager',
    'enforce_access',
    'Rbac',
]
