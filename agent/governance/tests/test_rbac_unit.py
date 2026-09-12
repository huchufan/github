import pytest
from agent.governance.core.rbac import RBACManager
from agent.core.types import Role, Permission


def test_rbac_check_and_modify():
    mgr = RBACManager()
    # existing roles
    assert mgr.check_permission(Role.ADMIN, Permission.AUDIT_LOG)
    # revoke and check
    mgr.revoke_permission(Role.ADMIN, Permission.AUDIT_LOG)
    assert not mgr.check_permission(Role.ADMIN, Permission.AUDIT_LOG)
    # grant back
    mgr.grant_permission(Role.ADMIN, Permission.AUDIT_LOG)
    assert mgr.check_permission(Role.ADMIN, Permission.AUDIT_LOG)

