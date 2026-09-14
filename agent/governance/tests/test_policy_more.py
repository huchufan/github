import pytest

from agent.core.types import (Actor, ExecutionContext, Operation,
                              OperationResult, Resource)
from agent.governance.core.policy import (Policy, PolicyCondition, PolicyLimit,
                                          PolicyValidator, RuleDecision,
                                          RuleEngine)


def make_actor(id="actor1", role="developer"):
    return Actor(id=id, role=role)


def make_resource():
    return Resource(type="service", owner="owner1", classification="INTERNAL")


def test_rule_engine_and_logic_and_or():
    engine = RuleEngine()
    p = Policy(
        id="p1",
        name="test",
        conditions=[
            PolicyCondition(field="role", operator="eq", value="admin"),
            PolicyCondition(field="resource.type", operator="eq", value="service"),
        ],
        condition_logic="AND",
    )
    rd = engine.evaluate_rule(p, {"role": "admin", "resource": {"type": "service"}})
    assert rd.passed
    # OR logic
    p.condition_logic = "OR"
    rd2 = engine.evaluate_rule(p, {"role": "user", "resource": {"type": "service"}})
    assert rd2.passed


def test_policy_validator_detects_failed_condition_and_limit():
    pv = PolicyValidator()
    # policy applies to 'delete' action only
    policy = Policy(
        id="p-delete",
        name="del",
        applies_to=["delete"],
        conditions=[PolicyCondition(field="role", operator="eq", value="admin")],
        limits=[PolicyLimit(limit_type="requests", max_count=1)],
    )
    pv.register_policy(policy)
    actor = Actor(id="u1", role="user")
    res = Resource(type="file", owner="owner")
    ctx = ExecutionContext(request_id="r1")
    op = Operation(action="delete", actor=actor, resource=res, context=ctx)
    result = pv.validate_operation(op)
    # expect a violation and that action is not ALLOW
    assert result.violations
    assert result.action != "ALLOW"
    assert any(v.policy_id == "p-delete" for v in result.violations)

    # test exceeds_limit: simulate usage
    pv.usage_counters = {actor.id: {"requests": 1}}
    res2 = pv.validate_operation(op)
    assert res2.violations
    assert any(v.limit is not None for v in res2.violations)


def test_record_usage_and_determine_action():
    pv = PolicyValidator()
    # create policy that will produce HIGH severity violation
    policy = Policy(
        id="p2",
        name="high",
        applies_to=["update"],
        conditions=[PolicyCondition(field="role", operator="eq", value="admin")],
        violation_severity="HIGH",
    )
    pv.register_policy(policy)
    actor = Actor(id="a2", role="user")
    op = Operation(action="update", actor=actor)
    res = pv.validate_operation(op)
    assert res.action in ("WARN", "REQUIRE_APPROVAL", "DENY")
    # record usage increments counter
    pv.record_usage(actor.id, "requests")
    assert pv.usage_counters[actor.id]["requests"] == 1
