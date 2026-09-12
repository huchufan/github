import pytest
from datetime import datetime, timedelta, timezone

from agent.governance.core.audit import AuditLogger, AuditAnalyzer, AnomalyReport
from agent.core.types import Actor, Resource, OperationResult, ExecutionContext


def make_actor(role='user', id='a1'):
    return Actor(id=id, role=role, organization='org')


def make_resource(classification='INTERNAL'):
    return Resource(type='file', owner='owner1', classification=classification)


def make_context():
    return ExecutionContext(request_id='r1', source_ip='10.0.0.1')


def test_log_operation_appends_and_alerts_on_failure():
    al = AuditLogger()
    actor = make_actor()
    res = make_resource()
    ctx = make_context()
    reslt = OperationResult(status='FAILURE', code=123, error='boom')

    record = al.log_operation('modify', actor, res, 'do', reslt, ctx)
    assert record in al.records
    assert record in al.immutable_log
    assert len(al.alerts) == 1


def test_should_alert_sensitive_data():
    al = AuditLogger()
    actor = make_actor()
    res = make_resource(classification='CONFIDENTIAL')
    ctx = make_context()
    reslt = OperationResult(status='SUCCESS', code=0)
    record = al.log_operation('read', actor, res, 'read', reslt, ctx)
    assert al.should_alert(record)


def test_audit_analyzer_detect_privilege_escalation():
    al = AuditLogger()
    actor_guest = make_actor(role='guest', id='g1')
    res = make_resource()
    ctx = make_context()
    reslt = OperationResult(status='SUCCESS')
    # guest attempts high risk op
    al.log_operation('policy:manage', actor_guest, res, 'attempt', reslt, ctx)
    analyzer = AuditAnalyzer(al)
    anomalies = analyzer.detect_privilege_escalation(al.records)
    assert any(a.type == 'PRIVILEGE_ESCALATION' for a in anomalies)


def test_generate_compliance_report_empty_window():
    al = AuditLogger()
    analyzer = AuditAnalyzer(al)
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc)
    report = analyzer.generate_compliance_report(start, end, 'p1')
    assert report.audit_coverage == 0.0
