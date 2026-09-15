"""
Auto-generated test for layers
"""

import pytest

from agent.memory.core.layers import Layers


def test_layers_init():
    inst = Layers()
    assert inst.config == {}


def test_layers_execute():
    inst = Layers()
    r = inst.execute()
    assert r.get("ok") is True
