"""
Auto-generated test for scheduler
"""
import pytest
from agent.automation.core.scheduler import Scheduler


def test_scheduler_init():
    inst = Scheduler()
    assert inst.config == {}


def test_scheduler_execute():
    inst = Scheduler()
    r = inst.execute()
    assert r.get('ok') is True
