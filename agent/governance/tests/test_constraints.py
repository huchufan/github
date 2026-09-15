"""
Auto-generated test for constraints
"""

import pytest

from agent.governance.core.constraints import Constraints


def test_constraints_init():
    inst = Constraints()
    assert inst.config == {}


def test_constraints_execute():
    inst = Constraints()
    r = inst.execute()
    assert r.get("ok") is True
