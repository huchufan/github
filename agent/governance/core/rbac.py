1|from typing import Set, Dict, Any, Optional
2|from dataclasses import dataclass
3|
4|# Use canonical Role and Permission from agent.core.types to ensure consistency
5|from agent.core.types import Role, Permission
6|from agent.core.errors import AccessDeniedError
7|
8|@dataclass
9|class AccessRule:
10|    # PoC AccessRule matching test construction (effect, conditions, deny_reason, priority)
11|    effect: str = "ALLOW"
12|    conditions: list = None
13|    deny_reason: str = ""
14|    priority: int = 0
15|    role: Optional[Role] = None
16|    permission: Optional[Permission] = None
17|    resource: str = "*"
18|
19|# sensible default permissions map
20|DEFAULT_ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
21|    Role.ADMIN: set(p for p in Permission),
22|    Role.DEVELOPER: {Permission.EXECUTE_AGENT, Permission.READ_MEMORY},
23|    Role.USER: {Permission.EXECUTE_AGENT},
24|    Role.GUEST: {Permission.QUERY_READONLY},
25|}
26|
27|class GovernancePolicy:
28|    """Minimal policy container"""
29|    def __init__(self, rules=None):
30|        self.rules = rules or []
31|
32|    def allows(self, role: Role, permission: Permission, resource: str = "*") -> bool:
33|        # simple check against defaults then explicit rules
34|        if permission in DEFAULT_ROLE_PERMISSIONS.get(role, set()):
35|            return True
36|        for r in self.rules:
37|            if r.role == role and r.permission == permission and (r.resource == resource or r.resource == "*"):
38|                return True
39|        return False
40|
41|    def add_rule(self, rule: AccessRule):
42|        # append an AccessRule-like object to rules for deny/allow evaluation
43|        self.rules.append(rule)
44|
45|    def evaluate_access(self, subject, action: str, resource, ctx):
        """Evaluate access via rules (ABAC) first, then RBAC defaults.
        Returns a decision-like object with .allow, .audit_code and .reason.
        """
        # First, evaluate explicit ABAC rules (self.rules). Rules are AccessRule-like objects
        for rule in getattr(self, 'rules', []):
            try:
                if getattr(rule, 'conditions', None):
                    ok = True
                    for cond in rule.conditions:
                        # cond can be a dict or an object with left/operator/right
                        if isinstance(cond, dict):
                            left = cond.get('left')
                            op = cond.get('operator')
                            right = cond.get('right')
                        else:
                            left = getattr(cond, 'left', None) or getattr(cond, 'key', None)
                            op = getattr(cond, 'operator', None) or getattr(cond, 'op', None)
                            right = getattr(cond, 'right', None) or getattr(cond, 'value', None)
                        # resolve left
                        val = None
                        if isinstance(left, str) and left.startswith('$subject_'):
                            attr = left[len('$subject_'):]
                            val = getattr(subject, attr, None)
                        elif isinstance(left, str) and left.startswith('$resource_'):
                            attr = left[len('$resource_'):]
                            val = getattr(resource, attr, None) if resource is not None else None
                        else:
                            # attempt to read dotted path from subject or resource
                            if isinstance(left, str) and '.' in left:
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
                        # compare
                        if op in ('eq','=='):
                            if val != right:
                                ok = False
                                break
                        elif op in ('ne','!='):
                            if val == right:
                                ok = False
                                break
                        else:
                            # unsupported operator -> fail the condition
                            ok = False
                            break
                    if ok:
                        # rule matches
                        if getattr(rule, 'effect', '').upper() == 'DENY':
                            return type('D', (), {'allow': False, 'audit_code': 'ACCESS_DENIED', 'reason': getattr(rule, 'deny_reason', '')})()
                        elif getattr(rule, 'effect', '').upper() == 'ALLOW':
                            return type('D', (), {'allow': True, 'audit_code': 'ACCESS_GRANTED', 'reason': ''})()
            except Exception:
                # ignore rule errors in PoC
                pass
        # Fallback: map action to permission and check RBAC defaults
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
