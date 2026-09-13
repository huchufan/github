"""
Auto-generated test for distribution
"""
import pytest
from agent.multiagent.core.distribution import Distribution


def test_distribution_init():
    inst = Distribution()
    assert inst.config == {}


def test_distribution_execute():
    inst = Distribution()
    r = inst.execute()
    assert r.get('ok') is True
