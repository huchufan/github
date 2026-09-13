"""
Auto-generated test for cluster
"""
import pytest
from agent.multiagent.core.cluster import Cluster


def test_cluster_init():
    inst = Cluster()
    assert inst.config == {}


def test_cluster_execute():
    inst = Cluster()
    r = inst.execute()
    assert r.get('ok') is True
