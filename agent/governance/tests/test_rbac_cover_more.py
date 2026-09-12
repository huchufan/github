import pytest

from agent.governance.core.rbac import RBACManager, GovernancePolicy, AccessRule
from agent.core.types import Actor, Resource, ExecutionContext, Role, Permission
from agent.core.types import AccessDecision


def test_rbac_grant_revoke_and_check():
    mgr = RBACManager()
    # ensure developer role has some permissions
    perms = mgr.get_permissions(Role.DEVELOPER)
    assert isinstance(perms, set)
    # grant a new permission to GUEST and verify
    mgr.grant_permission(Role.GUEST, Permission.SKILL_EXPLORE)
    assert mgr.check_permission(Role.GUEST, Permission.SKILL_EXPLORE)
    # revoke it
    mgr.revoke_permission(Role.GUEST, Permission.SKILL_EXPLORE)
    assert not mgr.check_permission(Role.GUEST, Permission.SKILL_EXPLORE)


def test_resolve_role_unknown_returns_guest():
    mgr = RBACManager()
    resolved = mgr.resolve_role('nonexistent_role')
    assert resolved == Role.GUEST


def test_governance_policy_rbac_denies_when_missing_permission():
    policy = GovernancePolicy()
    subj = Actor(id='a1', role=Role.USER.value)
    res = Resource(type='generic', owner='u1')
    ctx = ExecutionContext()
    # action that maps to a permission the USER likely doesn't have: policy._action_to_permission('config:modify_system')
    decision = policy.evaluate_access(subj, 'config:modify_system', res, ctx)
    assert decision.allow is False
    assert decision.audit_code in ('ACCESS_DENIED_RBAC', 'ACCESS_DENIED')


def test_governance_policy_abac_rule_deny():
    policy = GovernancePolicy()
    # add an explicit deny rule if subject_org == 'blocked'
    rule = AccessRule(effect='DENY', conditions=[{"left": "$subject_org", "operator": "eq", "right": "blocked"}], deny_reason='Org blocked', priority=10)
    policy.add_rule(rule)
    subj = Actor(id='a2', role=Role.USER.value, organization='blocked')
    res = Resource(type='generic', owner='u2')
    ctx = ExecutionContext()
    dec = policy.evaluate_access(subj, 'agent:execute', res, ctx)
    assert dec.allow is False
    assert dec.reason == 'Org blocked'

