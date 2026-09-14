"""
Auto-generated test for planner
"""

import pytest

from agent.orchestration.core.planner import Planner


def test_planner_init():
    inst = Planner()
    assert inst.config == {}


def test_planner_execute():
    inst = Planner()
    r = inst.execute()
    assert r.get("ok") is True
