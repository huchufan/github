"""
Auto-generated test for user_model
"""
import pytest
from agent.memory.core.user_model import UserModel


def test_user_model_init():
    inst = UserModel()
    assert inst.config == {}


def test_user_model_execute():
    inst = UserModel()
    r = inst.execute()
    assert r.get('ok') is True
