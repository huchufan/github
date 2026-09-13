"""
Auto-generated test for optimizer
"""
import pytest
from agent.evolution.core.optimizer import Optimizer


def test_optimizer_init():
    inst = Optimizer()
    assert inst.config == {}


def test_optimizer_execute():
    inst = Optimizer()
    r = inst.execute()
    assert r.get('ok') is True
