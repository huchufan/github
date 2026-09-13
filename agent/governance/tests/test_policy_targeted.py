import pytest

from agent.governance.core.policy import Policy, PolicyCondition, PolicyLimit, PolicyValidator, PolicyViolation, ValidationResult, Policy
from agent.core.types import Actor, Resource, Operation, ExecutionContext


def test_policy_validator_detects_failed_condition_and_limit():
    pv = PolicyValidator()
    policy = Policy(id='p-delete', applies_to=['delete'], conditions=[PolicyCondition(field='role', operator='eq', value='admin')], limits=[PolicyLimit(limit_type='requests', max_count=1)])
    pv.register_policy(policy)
    actor = Actor(id='u1', role='user')
    res = Resource(type='file', owner='owner')
    ctx = ExecutionContext(request_id='r1')
    op = Operation(action='delete', actor=actor, resource=res, context=ctx)
    result = pv.validate_operation(op)
    assert result.violations
    assert result.action != 'ALLOW'
