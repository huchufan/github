"""
Auto-generated test for governance_extra_013
"""
import pytest
from agent.governance.core.governance_extra_013 import GovernanceExtra013


def test_governance_extra_013_init():
    inst = GovernanceExtra013()
    assert inst.config == {}


def test_governance_extra_013_execute():
    inst = GovernanceExtra013()
    r = inst.execute()
    assert r.get('ok') is True
