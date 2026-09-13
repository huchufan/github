"""
Auto-generated test for communication
"""
import pytest
from agent.multiagent.core.communication import Communication


def test_communication_init():
    inst = Communication()
    assert inst.config == {}


def test_communication_execute():
    inst = Communication()
    r = inst.execute()
    assert r.get('ok') is True
