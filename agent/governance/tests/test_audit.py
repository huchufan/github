import pytest
from agent.governance.core.audit import AuditLog


def test_audit_record_and_query():
    log = AuditLog()
    r1 = log.record(actor='alice', action='create', resource_type='file', resource_id='f1', result={'ok': True}, success=True)
    r2 = log.record(actor='bob', action='delete', resource_type='file', resource_id='f2', result={'ok': False}, success=False)

    assert r1.actor == 'alice'
    assert r2.success is False

    all_records = log.to_dicts()
    assert isinstance(all_records, list)
    assert len(all_records) >= 2

    alice = log.query(actor='alice')
    assert len(alice) == 1

    failures = log.query(success=False)
    assert any(r.success is False for r in failures)
