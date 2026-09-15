import pytest
from agent.multiagent import get_agent, AGENT_REGISTRY


def test_get_agent_existing():
    a = get_agent('code_engineer')
    assert a is not None
    assert a['name'] == 'CodeEngineer'
    # enriched fields
    assert 'profile' in a
    assert 'soul' in a
    assert 'skill_text' in a


def test_registry_keys():
    assert 'code_engineer' in AGENT_REGISTRY
