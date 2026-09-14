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
    'developer': ['EXECUTE_AGENT', 'READ_MEMORY'],
    'user': ['EXECUTE_AGENT'],
    'guest': [],
}

@dataclass
class GovernancePolicy:
    name: str
    rules: list


def enforce_access(role: Role, permission: Permission) -> bool:
    """Simple enforcement PoC: check DEFAULT_ROLE_PERMISSIONS mapping"""
    allowed = DEFAULT_ROLE_PERMISSIONS.get(role.value, [])
    return permission.name in allowed


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
