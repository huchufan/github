import pytest
from agent.orchestration.core.condition import ConditionEvaluator
from agent.core.types import Condition


def make_cond(left, op, right):
    c = Condition()
    c.type = 'COMPARISON'
    c.left = left
    c.operator = op
    c.right = right
    return c


def test_evaluate_eq():
    ev = ConditionEvaluator()
    cond = make_cond(1, '==', 1)
    assert ev.evaluate_condition(cond, {})


def test_resolve_path():
    ev = ConditionEvaluator()
    class S: pass
    s = {'variables': {'x': 5}}
    cond = make_cond('$variables.x', '==', 5)
    assert ev.evaluate_condition(cond, s)
