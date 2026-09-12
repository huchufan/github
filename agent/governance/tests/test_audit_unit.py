import asyncio
from agent.governance.core.audit import AuditLogger, AuditAnalyzer
from agent.core.types import Actor, Resource, ExecutionContext, OperationResult
from datetime import datetime, timedelta


def test_audit_log_and_query():
    logger = AuditLogger()
    actor = Actor(id='u1', role='user')
    resource = Resource(type='doc', id='r1', owner='u1', classification='INTERNAL')
    ctx = ExecutionContext(request_id='req1')
    result = OperationResult(status='SUCCESS', code=0)

    rec = logger.log_operation('read', actor, resource, 'read doc', result, ctx)
    assert rec.actor_id == actor.id
    found = logger.query(actor_id='u1')
    assert len(found) >= 1


def test_audit_analyzer_detect_privilege_escalation():
    logger = AuditLogger()
    analyzer = AuditAnalyzer(logger)
    # create a low-role actor performing high-risk op
    actor = Actor(id='u2', role='guest')
    resource = Resource(type='config', id='c1', owner='admin', classification='INTERNAL')
    ctx = ExecutionContext(request_id='r2')
    fail_result = OperationResult(status='FAILURE', code=1, error='denied')
    # log a high risk op
    logger.log_operation('policy:manage', actor, resource, 'try manage', fail_result, ctx)
    anomalies = analyzer.detect_privilege_escalation(logger.records)
    assert any(a.type == 'PRIVILEGE_ESCALATION' for a in anomalies)
