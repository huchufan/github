"""
Auto-generated test for fusion
"""

import pytest

from agent.memory.core.fusion import Fusion


def test_fusion_init():
    inst = Fusion()
    assert inst.config == {}


def test_fusion_execute():
    inst = Fusion()
    r = inst.execute()
    assert r.get("ok") is True
