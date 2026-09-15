from datetime import timedelta

import pytest

from mesh_manager import MeshManager


def test_register_and_list_and_get_agent():
    mm = MeshManager()
    a = mm.register_agent("a1")
    assert mm.get_agent("a1") is not None
    assert "a1" in [x.agent_id for x in mm.list_agents()]


def test_heartbeat_and_mark_dead():
    mm = MeshManager()
    a = mm.register_agent("a2")
    assert mm.heartbeat("a2")
    # mark dead with stale_after=0s to force dead
    dead = mm.mark_dead_if_stale(stale_after=timedelta(seconds=0))
    assert "a2" in dead


def test_rebalance_load():
    mm = MeshManager()
    mm.register_agent("a1").load = 1.0
    mm.register_agent("a2").load = 3.0
    dist = mm.rebalance_load()
    assert dist["a1"] == dist["a2"]
