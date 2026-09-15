"""
Auto-generated test for multiagent_extra_018
"""
import pytest
from agent.multiagent.core.multiagent_extra_018 import MultiagentExtra018


def test_multiagent_extra_018_init():
    inst = MultiagentExtra018()
    assert inst.config == {}


def test_multiagent_extra_018_execute():
    inst = MultiagentExtra018()
    r = inst.execute()
    assert r.get('ok') is True
