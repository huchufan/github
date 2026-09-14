"""
Auto-generated test for distiller
"""

import pytest

from agent.evolution.core.distiller import Distiller


def test_distiller_init():
    inst = Distiller()
    assert inst.config == {}


def test_distiller_execute():
    inst = Distiller()
    r = inst.execute()
    assert r.get("ok") is True
