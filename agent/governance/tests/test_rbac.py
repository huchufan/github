import pytest
from agent.governance.core.rbac import RBACManager, Role, Permission


def test_rbac_initial_permissions():
    mgr = RBACManager()
    assert mgr.check_permission(Role.ADMIN, Permission.AUDIT_LOG)
    assert mgr.check_permission(Role.DEVELOPER, Permission.EXECUTE_AGENT)
    assert not mgr.check_permission(Role.GUEST, Permission.EXECUTE_AGENT)


def test_grant_and_revoke_permission():
    mgr = RBACManager()
    assert not mgr.check_permission(Role.GUEST, Permission.READ_MEMORY)
    mgr.grant_permission(Role.GUEST, Permission.READ_MEMORY)
    assert mgr.check_permission(Role.GUEST, Permission.READ_MEMORY)
    mgr.revoke_permission(Role.GUEST, Permission.READ_MEMORY)
    assert not mgr.check_permission(Role.GUEST, Permission.READ_MEMORY)
