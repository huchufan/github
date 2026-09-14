from typing import Set, Dict
from enum import Enum

class Role(Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    GUEST = "guest"

class Permission(Enum):
    EXECUTE_AGENT = "agent:execute"
    READ_MEMORY = "memory:read"
    WRITE_CONFIG = "config:write"
    AUDIT_LOG = "audit:read"

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
