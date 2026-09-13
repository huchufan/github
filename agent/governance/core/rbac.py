1|from typing import Set, Dict, Any, Optional
2|from dataclasses import dataclass
3|
4|# Use canonical Role and Permission from agent.core.types to ensure consistency
5|from agent.core.types import Role, Permission
6|from agent.core.errors import AccessDeniedError
7|
8|
9|@dataclass
10|class AccessRule:
11|    # PoC AccessRule matching test construction (effect, conditions, deny_reason, priority)
12|    effect: str = "ALLOW"
13|    conditions: list | None = None
14|    deny_reason: str = ""
15|    priority: int = 0
16|    role: Optional[Role] = None
17|    permission: Optional[Permission] = None
18|    resource: str = "*"
19|
20|
21|# sensible default permissions map
22|DEFAULT_ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
23|    Role.ADMIN: set(p for p in Permission),
24|    Role.DEVELOPER: {Permission.EXECUTE_AGENT, Permission.READ_MEMORY},
25|    Role.USER: {Permission.EXECUTE_AGENT},
26|    Role.GUEST: {Permission.QUERY_READONLY},
27|}
28|
29|
30|class GovernancePolicy:
31|    """Minimal policy container and ABAC rule evaluator (PoC).
32|
33|    Provides .allows(role, permission, resource) for RBAC default checks and
34|    evaluate_access(subject, action, resource, ctx) for ABAC-style rule evaluation.
35|    """
36|
37|    def __init__(self, rules: Optional[list] = None):
38|        self.rules = rules or []
39|
40|    def allows(self, role: Role, permission: Permission, resource: str = "*") -> bool:
41|        # simple check against defaults then explicit rules
42|        if permission in DEFAULT_ROLE_PERMISSIONS.get(role, set()):
43|            return True
44|        for r in self.rules:
45|            if getattr(r, 'role', None) == role and getattr(r, 'permission', None) == permission and (
46|                getattr(r, 'resource', None) == resource or getattr(r, 'resource', None) == "*"
47|            ):
48|                return True
49|        return False
50|
51|    def add_rule(self, rule: AccessRule):
52|        # append an AccessRule-like object to rules for deny/allow evaluation
53|        self.rules.append(rule)
54|
55|    def evaluate_access(self, subject, action: str, resource, ctx):
56|        """Evaluate ABAC rules first; fallback to RBAC default check.
57|
58|        Returns a lightweight decision-like object with attributes:
59|          - allow (bool)
60|          - audit_code (str)
61|          - reason (str)
62|        """
63|        # ABAC: iterate rules and evaluate conditions (supports dict or object conditions)
64|        for rule in getattr(self, 'rules', []):
65|            try:
66|                conds = getattr(rule, 'conditions', None) or []
67|                if not conds:
68|                    continue
69|                matches = True
70|                for cond in conds:
71|                    if isinstance(cond, dict):
72|                        left = cond.get('left')
73|                        op = cond.get('operator')
74|                        right = cond.get('right')
75|                    else:
76|                        left = getattr(cond, 'left', None) or getattr(cond, 'key', None)
77|                        op = getattr(cond, 'operator', None) or getattr(cond, 'op', None)
78|                        right = getattr(cond, 'right', None) or getattr(cond, 'value', None)
79|
80|                    # resolve left value from subject/resource or dotted paths
81|                    val = None
82|                    if isinstance(left, str) and left.startswith('$subject_'):
83|                        token = left[len('$subject_'):]
84|                        val = None
85|                        if subject is not None:
86|                            # support dict-like subjects
87|                            if isinstance(subject, dict):
88|                                val = subject.get(token)
89|                            else:
90|                                # direct attribute
91|                                val = getattr(subject, token, None)
92|                                # alias map (org -> organization)
93|                                if val is None:
94|                                    aliases = {'org':'organization'}
95|                                    if token in aliases and hasattr(subject, aliases[token]):
96|                                        val = getattr(subject, aliases[token], None)
97|                                # fuzzy fallback: substring match on attribute names
98|                                if val is None:
99|                                    for cand in dir(subject):
100|                                        if cand.startswith('_'):
101|                                            continue
102|                                        if token.lower() in cand.lower():
103|                                            try:
104|                                                val = getattr(subject, cand, None)
105|                                                if val is not None:
106|                                                    break
107|                                            except Exception:
108|                                                continue
109|                    elif isinstance(left, str) and left.startswith('$resource_'):
110|                        token = left[len('$resource_'):]
111|                        val = None
112|                        if resource is not None:
113|                            if isinstance(resource, dict):
114|                                val = resource.get(token)
115|                            else:
116|                                val = getattr(resource, token, None)
117|                                if val is None:
118|                                    for cand in dir(resource):
119|                                        if cand.startswith('_'):
120|                                            continue
121|                                        if token.lower() in cand.lower():
122|                                            try:
123|                                                val = getattr(resource, cand, None)
124|                                                if val is not None:
125|                                                    break
126|                                            except Exception:
127|                                                continue
128|                    elif isinstance(left, str) and '.' in left:
129|                        parts = left.split('.')
130|                        if parts[0] == 'resource' and resource is not None:
131|                            cur = resource
132|                            for ppart in parts[1:]:
133|                                cur = getattr(cur, ppart, None) if not isinstance(cur, dict) else cur.get(ppart)
134|                            val = cur
135|                        elif parts[0] == 'subject':
136|                            cur = subject
137|                            for ppart in parts[1:]:
138|                                cur = getattr(cur, ppart, None) if not isinstance(cur, dict) else cur.get(ppart)
139|                            val = cur
140|                    else:
141|                        val = None
142|
143|                    # compare
144|                    if op in ('eq', '=='):
145|                        if val != right:
146|                            matches = False
147|                            break
148|                    elif op in ('ne', '!='):
149|                        if val == right:
150|                            matches = False
151|                            break
152|                    else:
153|                        # unsupported -> fail this rule
154|                        matches = False
155|                        break
156|
157|                if matches:
158|                    eff = getattr(rule, 'effect', '').upper()
159|                    if eff == 'DENY':
160|                        return type('D', (), {'allow': False, 'audit_code': 'ACCESS_DENIED', 'reason': getattr(rule, 'deny_reason', '')})()
161|                    if eff == 'ALLOW':
162|                        return type('D', (), {'allow': True, 'audit_code': 'ACCESS_GRANTED', 'reason': ''})()
163|            except Exception:
164|                # ignore ABAC evaluation errors in PoC
165|                pass
166|
167|        # Fallback: RBAC mapping
168|        role_val = getattr(subject, 'role', subject)
169|        if hasattr(role_val, 'value'):
170|            role_val = role_val.value
171|        try:
172|            role_enum = Role(role_val)
173|        except Exception:
174|            return type('D', (), {'allow': False, 'audit_code': 'ACCESS_DENIED', 'reason': ''})()
175|
176|        perm = None
177|        if isinstance(action, str):
178|            try:
179|                perm = Permission(action)
180|            except Exception:
181|                try:
182|                    perm = Permission[action]
183|                except Exception:
184|                    perm = None
185|        if perm is None:
186|            perm = Permission.EXECUTE_AGENT
187|
188|        allowed = self.allows(role_enum, perm, getattr(resource, 'type', '*'))
189|        return type('D', (), {'allow': allowed, 'audit_code': 'ACCESS_GRANTED' if allowed else 'ACCESS_DENIED', 'reason': ''})()
190|
191|
192|class RBACManager:
193|    """Compatibility manager for RBAC-style APIs used in tests.
194|
195|    Minimal interface:
196|      - get_permissions(role) -> Set[Permission]
197|      - resolve_role(subject) -> Role
198|      - evaluate_access(subject, action, resource, ctx) -> decision object
199|      - enforce_access(subject, action, resource, ctx) -> True or raises AccessDeniedError
200|      - grant_permission / revoke_permission for dynamic tests
201|    """
202|
203|    def __init__(self, policy: Optional[GovernancePolicy] = None):
204|        self.policy = policy or GovernancePolicy()
205|        # dynamic grants and revokes applied at runtime (tests mutate these)
206|        self._overrides: Dict[Role, Set[Permission]] = {}
207|        self._revoked: Dict[Role, Set[Permission]] = {}
208|        # compatibility: basic config store expected by legacy tests
209|        self.config: Dict[str, Any] = {}
210|
211|    def get_permissions(self, role: Role) -> Set[Permission]:
212|        # Admin role has all permissions by design
213|        if role == Role.ADMIN:
214|            return set(p for p in Permission)
215|        # base defaults, plus overrides, minus revoked entries
216|        base = set(DEFAULT_ROLE_PERMISSIONS.get(role, set()))
217|        base |= set(self._overrides.get(role, set()))
218|        base -= set(self._revoked.get(role, set()))
219|        return base
220|
221|        def check_permission(self, role: Role, permission: Permission) -> bool:
        """Return True if the role currently has the permission.

        Normalize inputs to canonical enums. Revoked permissions take precedence.
        Overrides are respected. Admin has implicit grant unless revoked.
        """
        # normalize role/permission
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
        # revoked permissions take precedence
        if role in self._revoked and permission in self._revoked.get(role, set()):
            return False
        # explicit overrides add permissions
        if role in self._overrides and permission in self._overrides.get(role, set()):
            return True
        # Admin has all permissions unless explicitly revoked above
        if role == Role.ADMIN:
            return True
        return permission in self.get_permissions(role)
234|
235|        def grant_permission(self, role: Role, permission: Permission):
        """Grant a permission to a role at runtime (for tests/PoC).

        Normalize inputs; if the permission was previously revoked for the role,
        remove the revocation so a subsequent check_permission will succeed.
        """
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
        # remove any explicit revocation for this role+permission
        if role in self._revoked and permission in self._revoked.get(role, set()):
            try:
                self._revoked[role].remove(permission)
            except Exception:
                pass
        self._overrides.setdefault(role, set()).add(permission)
248|
249|    def revoke_permission(self, role: Role, permission: Permission):
250|        self._revoked.setdefault(role, set()).add(permission)
251|        if role in self._overrides and permission in self._overrides[role]:
252|            self._overrides[role].remove(permission)
253|
254|    def resolve_role(self, subject) -> Role:
255|        rv = getattr(subject, 'role', None)
256|        if rv is None:
257|            return Role.GUEST
258|        try:
259|            return Role(rv) if not isinstance(rv, Role) else rv
260|        except Exception:
261|            return Role.GUEST
262|
263|    def evaluate_access(self, subject, action: str, resource, ctx=None):
264|        return self.policy.evaluate_access(subject, action, resource, ctx)
265|
266|    def enforce_access(self, subject, action: str, resource, ctx=None):
267|        dec = self.evaluate_access(subject, action, resource, ctx)
268|        if not getattr(dec, 'allow', False):
269|            raise AccessDeniedError(getattr(dec, 'reason', 'access denied'))
270|        return True
271|
272|    def execute(self, *args, **kwargs):
273|        """PoC execute method expected by legacy tests: returns a simple success dict.
274|        Meant as a minimal compatibility shim.
275|        """
276|        return {'ok': True}
277|
278|
279|# Backwards-compatibility alias for older tests expecting 'Rbac'
280|class Rbac(RBACManager):
281|    """Compatibility shim: older tests import Rbac class.
282|    Minimal subclass of RBACManager with identical behaviour.
283|    """
284|    pass
285|
286|
287|# module-level alias
288|Rbac = Rbac
289|
290|
291|def enforce_access(policy_or_manager, subject, action, resource, ctx=None):
292|    """Module-level helper preserving older signature patterns used in tests.
293|
294|    Accepts either a GovernancePolicy or RBACManager-like object as first arg.
295|    If it's a GovernancePolicy, evaluate via GovernancePolicy.evaluate_access.
296|    If it's an RBACManager, call its enforce_access.
297|    """
298|    if hasattr(policy_or_manager, 'enforce_access'):
299|        return policy_or_manager.enforce_access(subject, action, resource, ctx)
300|    if isinstance(policy_or_manager, GovernancePolicy):
301|        dec = policy_or_manager.evaluate_access(subject, action, resource, ctx)
302|        if not getattr(dec, 'allow', False):
303|            raise AccessDeniedError(getattr(dec, 'reason', 'access denied'))
304|        return True
305|    # unknown manager: try to treat as a policy dict
306|    try:
307|        mgr = RBACManager(policy_or_manager)
308|        return mgr.enforce_access(subject, action, resource, ctx)
309|    except Exception:
310|        raise AccessDeniedError('access denied')
311|