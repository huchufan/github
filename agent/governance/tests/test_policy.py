"""
Auto-generated test for policy
"""

import pytest

from agent.governance.core.policy import Policy


def test_policy_init():
    inst = Policy()
    assert inst.config == {}


def test_policy_execute():
    inst = Policy()
    r = inst.execute()
    assert r.get("ok") is True
