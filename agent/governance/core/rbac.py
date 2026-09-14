from typing import Set, Dict, Optional
# Use shared Role/Permission types from agent.core.types so tests import the same enums
from agent.core.types import Role, Permission

from dataclasses import dataclass

@dataclass
class AccessRule:
    id: str
    role: str
    permission: str

DEFAULT_ROLE_PERMISSIONS = {
    'admin': [p.name for p in Permission],
    'developer': ['EXECUTE_AGENT','READ_MEMORY'],
    'user': ['EXECUTE_AGENT'],
    'guest': [],
}

@dataclass
class GovernancePolicy:
    name: str
    rules: list


def enforce_access(role: Role, permission: Permission) -> bool:
    """Simple enforcement PoC: check RBACManager default mapping"""
    allowed = DEFAULT_ROLE_PERMISSIONS.get(role.value, [])
    return permission.name in allowed


class RBACManager:
    """角色基础访问控制管理"""

    def __init__(self):
        self.roles: Dict[Role, Set[Permission]] = {
            Role.ADMIN: set(p for p in Permission),
            Role.DEVELOPER: {Permission.EXECUTE_AGENT, Permission.READ_MEMORY},
            Role.USER: {Permission.EXECUTE_AGENT},
            Role.GUEST: set(),
        }

    def check_permission(self, role: Role, permission: Permission) -> bool:
        """检查权限"""
-        return permission in self.roles.get(role, set())
+        perms = self.roles.get(role, set())
+        if isinstance(perms, list):
+            return permission.name in perms
+        return permission in perms
+
+    def get_permissions(self, role: Role) -> Set[Permission]:
+        perms = self.roles.get(role, set())
+        if isinstance(perms, list):
+            return set(Permission[p] for p in perms if p in Permission.__members__)
+        return perms
+
+    def resolve_role(self, role_name: str) -> Role:
+        try:
+            return Role(role_name)
+        except Exception:
+            return Role.GUEST

    def revoke_permission(self, role: Role, permission: Permission):
        """撤销权限"""
        if role in self.roles:
            self.roles[role].discard(permission)
