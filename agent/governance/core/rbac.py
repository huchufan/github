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
