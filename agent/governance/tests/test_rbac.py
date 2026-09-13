"""
Auto-generated test for rbac
"""
import pytest
from agent.governance.core.rbac import Rbac


def test_rbac_init():
    inst = Rbac()
    assert inst.config == {}


def test_rbac_execute():
    inst = Rbac()
    r = inst.execute()
    assert r.get('ok') is True
