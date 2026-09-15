from datetime import timedelta

import pytest

from mesh_manager import MeshManager


def test_register_and_list_and_get_agent():
    mm = MeshManager()
    a = mm.register_agent("a1")
    assert mm.get_agent("a1") is not None
    assert a.agent_id == "a1"
    assert mm.list_agents()


def test_heartbeat_and_mark_dead():
    mm = MeshManager()
    mm.register_agent("a1")
    assert mm.heartbeat("a1")
    # force last_heartbeat old
    mm.agents["a1"].last_heartbeat = mm.agents["a1"].last_heartbeat - timedelta(
        seconds=3600
    )
    dead = mm.mark_dead_if_stale(stale_after=timedelta(seconds=60))
    assert "a1" in dead


def test_rebalance_load():
    mm = MeshManager()
    mm.register_agent("a1")
    mm.register_agent("a2")
    mm.agents["a1"].load = 10
    mm.agents["a2"].load = 0
    res = mm.rebalance_load()
    assert res["a1"] == res["a2"]
