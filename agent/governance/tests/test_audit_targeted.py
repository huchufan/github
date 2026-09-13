import pytest
from datetime import datetime, timedelta

from agent.governance.core.audit import AuditLogger, AuditAnalyzer, AnomalyReport
from agent.core.types import Actor, Resource, ExecutionContext, OperationResult, AuditRecord


def test_audit_log_and_alert_handler_called():
    logger = AuditLogger()
    called = []
    def handler(alert):
        called.append(alert)

    logger.register_alert_handler(handler)
    actor = Actor(id='u1', role='user')
    res = Resource(type='file', owner='owner', classification='CONFIDENTIAL')
    ctx = ExecutionContext(request_id='r1')
    result = OperationResult(status='SUCCESS', code=0)

    rec = logger.log_operation('read', actor, res, 'read file', result, ctx)
    assert isinstance(rec, AuditRecord)
    # since involves_sensitive_data True, should alert
    assert logger.alerts, 'alerts should not be empty'
    assert called, 'handler should be called'


def test_audit_analyzer_privilege_escalation_and_failure_rate():
    logger = AuditLogger()
    ana = AuditAnalyzer(logger)

    # create records: one low-role performing high-risk op
    actor_low = Actor(id='low1', role='user')
    res = Resource(type='cfg', owner='owner', classification='INTERNAL')
    ctx = ExecutionContext(request_id='r2')
    fail_result = OperationResult(status='FAILURE', code=1, error='err')

    # high-risk op by low role
    logger.log_operation('policy:manage', actor_low, res, 'attempt', fail_result, ctx)

    # many sensitive accesses by same actor to trigger unusual access
    actor_s = Actor(id='s1', role='service')
    res_s = Resource(type='secret', owner='o', classification='CONFIDENTIAL')
    for i in range(55):
        logger.log_operation('read', actor_s, res_s, f'read {i}', OperationResult(status='SUCCESS', code=0), ctx)

    anomalies = ana.detect_anomalies(time_window=timedelta(days=1))
    types = [a.type for a in anomalies]
    assert 'PRIVILEGE_ESCALATION' in types
    assert any(t in types for t in ('UNUSUAL_ACCESS','HIGH_FAILURE_RATE'))
