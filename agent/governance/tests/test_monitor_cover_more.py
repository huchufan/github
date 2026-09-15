import pytest

from agent.governance.core.monitor import GovernanceAlert, GovernanceMonitor


class Op:
    def __init__(
        self,
        actor_role=None,
        action=None,
        operation_status=None,
        involves_sensitive_data=False,
    ):
        self.actor_role = actor_role
        self.action = action
        self.operation_status = operation_status
        self.involves_sensitive_data = involves_sensitive_data


def test_detect_privilege_and_alerting_called():
    gm = GovernanceMonitor()
    called = []
    gm.register_notify_handler(lambda a: called.append(a))

    op = Op(actor_role="user", action="policy:manage")
    alerts = gm.monitor_operations([op])
    assert any(a.category == "PRIVILEGE_ABUSE" for a in alerts)
    # CRITICAL should trigger notify handlers
    assert called


def test_detect_anomaly_and_compliance_violation():
    gm = GovernanceMonitor()
    op_fail = Op(
        actor_role="service", operation_status="FAILURE", involves_sensitive_data=True
    )
    alerts = gm.monitor_operations([op_fail])
    cats = [a.category for a in alerts]
    assert "ANOMALY" in cats or "COMPLIANCE_VIOLATION" in cats
