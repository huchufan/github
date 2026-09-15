"""治理框架测试"""

import asyncio

import pytest

from agent.core.errors import AccessDeniedError
from agent.core.types import (AccessDecision, Actor, ExecutionContext,
                              Operation, OperationResult, Permission, Resource,
                              Role)
from agent.governance.core.audit import AuditAnalyzer, AuditLogger
from agent.governance.core.constraints import (ExecutionConstraints,
                                               ResourceQuotaManager)
from agent.governance.core.monitor import GovernanceMonitor
from agent.governance.core.policy import (Policy, PolicyCondition,
                                          PolicyValidator)
from agent.governance.core.rbac import (AccessRule, GovernancePolicy,
                                        RBACManager, enforce_access)


class TestRBAC:
    def test_admin_has_all_permissions(self):
        rbac = RBACManager()
        assert rbac.check_permission(Role.ADMIN, Permission.EXECUTE_AGENT)
        assert rbac.check_permission(Role.ADMIN, Permission.MODIFY_SYSTEM)

    def test_guest_has_limited_permissions(self):
        rbac = RBACManager()
        assert not rbac.check_permission(Role.GUEST, Permission.EXECUTE_AGENT)
        assert rbac.check_permission(Role.GUEST, Permission.QUERY_READONLY)

    def test_grant_and_revoke(self):
        rbac = RBACManager()
        rbac.grant_permission(Role.GUEST, Permission.EXECUTE_AGENT)
        assert rbac.check_permission(Role.GUEST, Permission.EXECUTE_AGENT)
        rbac.revoke_permission(Role.GUEST, Permission.EXECUTE_AGENT)
        assert not rbac.check_permission(Role.GUEST, Permission.EXECUTE_AGENT)


class TestABAC:
    def test_default_deny(self):
        policy = GovernancePolicy()
        subject = Actor(role=Role.USER.value)
        resource = Resource(type="memory", owner="other")
        ctx = ExecutionContext()
        decision = policy.evaluate_access(subject, "memory:read", resource, ctx)
        assert not decision.allow

    def test_deny_rule_blocks(self):
        policy = GovernancePolicy()
        policy.add_rule(
            AccessRule(
                effect="DENY",
                conditions=[
                    {"operator": "eq", "left": "$subject_role", "right": "guest"},
                ],
                deny_reason="Guests are blocked",
                priority=10,
            )
        )
        subject = Actor(role=Role.GUEST.value)
        resource = Resource()
        ctx = ExecutionContext()
        decision = policy.evaluate_access(subject, "agent:execute", resource, ctx)
        assert not decision.allow

    def test_enforce_access_raises(self):
        policy = GovernancePolicy()
        subject = Actor(role=Role.GUEST.value)
        with pytest.raises(AccessDeniedError):
            enforce_access(
                policy, subject, "agent:execute", Resource(), ExecutionContext()
            )


class TestAudit:
    def test_log_operation(self):
        logger = AuditLogger()
        actor = Actor(role=Role.USER.value)
        resource = Resource(type="skill", classification="CONFIDENTIAL")
        ctx = ExecutionContext()
        result = OperationResult(status="SUCCESS")
        record = logger.log_operation(
            "skill:create", actor, resource, "create skill", result, ctx
        )
        assert record.audit_id.startswith("aud-")
        assert record.involves_sensitive_data
        assert len(logger.records) == 1

    def test_alert_on_sensitive(self):
        logger = AuditLogger()
        actor = Actor(role=Role.USER.value)
        resource = Resource(classification="SECRET")
        logger.log_operation(
            "data:export",
            actor,
            resource,
            "export",
            OperationResult(status="SUCCESS"),
            ExecutionContext(),
        )
        assert len(logger.alerts) == 1

    def test_compliance_report(self):
        logger = AuditLogger()
        analyzer = AuditAnalyzer(logger)
        from datetime import datetime, timedelta

        now = datetime.now()
        report = analyzer.generate_compliance_report(
            now - timedelta(days=1), now, "pol-001"
        )
        assert report.policy_id == "pol-001"
        assert report.log_integrity


class TestPolicy:
    def test_policy_validation_allow(self):
        validator = PolicyValidator()
        policy = Policy(
            id="pol-001",
            name="test",
            applies_to=["agent:execute"],
            conditions=[PolicyCondition(field="role", operator="ne", value="guest")],
        )
        validator.register_policy(policy)
        actor = Actor(role=Role.USER.value)
        op = Operation(action="agent:execute", actor=actor, resource=Resource())
        result = validator.validate_operation(op)
        assert result.allowed

    def test_policy_validation_deny(self):
        validator = PolicyValidator()
        policy = Policy(
            id="pol-001",
            name="test",
            applies_to=["agent:execute"],
            conditions=[PolicyCondition(field="role", operator="ne", value="guest")],
            violation_severity="CRITICAL",
        )
        validator.register_policy(policy)
        actor = Actor(role=Role.GUEST.value)
        op = Operation(action="agent:execute", actor=actor, resource=Resource())
        result = validator.validate_operation(op)
        assert result.action == "DENY"


class TestConstraints:
    def test_timeout_constraint(self):
        constraints = ExecutionConstraints()
        actor = Actor(role=Role.USER.value)
        op = Operation(estimated_duration=99999)
        result = constraints.check_constraints(op, actor)
        assert not result.passed
        assert result.violations[0].type == "timeout"

    def test_quota_manager(self):
        qm = ResourceQuotaManager({"user": {"storage": 100}})
        assert qm.check_quota("user", "storage", 50, 0)
        assert not qm.check_quota("user", "storage", 50, 80)


class TestMonitor:
    def test_privilege_abuse_detection(self):
        monitor = GovernanceMonitor()
        op = type("Op", (), {"actor_role": "guest", "action": "config:modify_system"})()
        assert monitor.detect_privilege_abuse(op) == "CRITICAL"

    def test_raise_alert(self):
        monitor = GovernanceMonitor()
        alert = monitor.raise_alert("CRITICAL", "PRIVILEGE_ABUSE", None)
        assert alert.level == "CRITICAL"
        assert len(monitor.alerts) == 1
