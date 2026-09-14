"""
Auto-generated test for triggers
"""

import pytest

from agent.automation.core.triggers import Triggers


def test_triggers_init():
    inst = Triggers()
    assert inst.config == {}


def test_triggers_execute():
    inst = Triggers()
    r = inst.execute()
    assert r.get("ok") is True
