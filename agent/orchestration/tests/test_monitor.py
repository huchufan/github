"""
Auto-generated test for monitor
"""
import pytest
from agent.orchestration.core.monitor import Monitor


def test_monitor_init():
    inst = Monitor()
    assert inst.config == {}


def test_monitor_execute():
    inst = Monitor()
    r = inst.execute()
    assert r.get('ok') is True
