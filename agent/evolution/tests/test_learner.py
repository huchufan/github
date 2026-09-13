"""
Auto-generated test for learner
"""
import pytest
from agent.evolution.core.learner import Learner


def test_learner_init():
    inst = Learner()
    assert inst.config == {}


def test_learner_execute():
    inst = Learner()
    r = inst.execute()
    assert r.get('ok') is True
