"""
Auto-generated test for dag
"""
import pytest
from agent.orchestration.core.dag import Dag


def test_dag_init():
    inst = Dag()
    assert inst.config == {}


def test_dag_execute():
    inst = Dag()
    r = inst.execute()
    assert r.get('ok') is True
