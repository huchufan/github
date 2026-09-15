import pytest

from agent.core.types import Condition
from agent.orchestration.core.condition import ConditionEvaluator


def test_comparison_operators_and_in():
    ev = ConditionEvaluator()
    # smoke: basic equality
    c = Condition(type="COMPARISON", left=1, operator="==", right=1)
    assert ev.evaluate_condition(c, {})


def test_comparisons_and_boolean_and_resolve():
    ev = ConditionEvaluator()
    # equality
    c_eq = Condition(type="COMPARISON", left=1, operator="==", right=1)
    assert ev.evaluate_condition(c_eq, {})
    # not equal
    c_ne = Condition(type="COMPARISON", left=1, operator="!=", right=2)
    assert ev.evaluate_condition(c_ne, {})
    # greater than
    c_gt = Condition(type="COMPARISON", left=5, operator=">", right=3)
    assert ev.evaluate_condition(c_gt, {})
    # less than
    c_lt = Condition(type="COMPARISON", left=2, operator="<", right=3)
    assert ev.evaluate_condition(c_lt, {})
    # greater equal
    c_ge = Condition(type="COMPARISON", left=3, operator=">=", right=3)
    assert ev.evaluate_condition(c_ge, {})
    # less equal
    c_le = Condition(type="COMPARISON", left=2, operator="<=", right=3)
    assert ev.evaluate_condition(c_le, {})
    # in operator: left in right
    c_in = Condition(type="COMPARISON", left="a", operator="in", right=["a", "b"])
    assert ev.evaluate_condition(c_in, {})


def test_boolean_logic_and_or():
    ev = ConditionEvaluator()
    a = Condition(type="COMPARISON", left=1, operator="==", right=1)
    b = Condition(type="COMPARISON", left=2, operator="==", right=2)
    parent_and = Condition(type="BOOLEAN_LOGIC", children=[a, b], logic="AND")
    assert ev.evaluate_condition(parent_and, {})
    parent_or = Condition(
        type="BOOLEAN_LOGIC",
        children=[a, Condition(type="COMPARISON", left=1, operator="==", right=2)],
        logic="OR",
    )
    assert ev.evaluate_condition(parent_or, {})


def test_state_check_and_resolve_value_with_paths():
    ev = ConditionEvaluator()
    # dict path
    state = {"variables": {"x": 10}}
    c = Condition(type="COMPARISON", left="$variables.x", operator="==", right=10)
    assert ev.evaluate_condition(c, state)

    # attribute path
    class S:
        pass

    s = S()
    s.variables = {"y": 5}
    c2 = Condition(type="COMPARISON", left="$variables.y", operator="==", right=5)
    assert ev.evaluate_condition(c2, s)


def test_state_check_truthy_falsey():
    ev = ConditionEvaluator()
    c_true = Condition(type="STATE_CHECK", left=True)
    assert ev.evaluate_condition(c_true, {})
    c_false = Condition(type="STATE_CHECK", left=False)
    assert not ev.evaluate_condition(c_false, {})


def test_metric_condition_delegates_to_comparison():
    ev = ConditionEvaluator()
    c = Condition(type="METRIC_BASED", left=4, operator=">", right=2)
    assert ev.evaluate_condition(c, {})
