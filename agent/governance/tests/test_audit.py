"""
Auto-generated test for audit
"""
import pytest
from agent.governance.core.audit import Audit


def test_audit_init():
    inst = Audit()
    assert inst.config == {}


def test_audit_execute():
    inst = Audit()
    r = inst.execute()
    assert r.get('ok') is True
