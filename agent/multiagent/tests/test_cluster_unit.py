import asyncio
import pytest
from agent.multiagent.core.cluster import AgentRegistry, AgentInfo, AgentConfig


def test_register_and_discover():
    registry = AgentRegistry()
    info = AgentInfo(id='a1', role='worker', capabilities=['task'])
    # register
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(registry.register_agent(info))
    # discover
    found = loop.run_until_complete(registry.discover_agents(role='worker'))
    assert any(a.id == 'a1' for a in found)


def test_unregister():
    registry = AgentRegistry()
    info = AgentInfo(id='a2', role='worker', capabilities=['task'])
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(registry.register_agent(info))
    loop.run_until_complete(registry.unregister_agent('a2'))
    with pytest.raises(Exception):
        loop.run_until_complete(registry.unregister_agent('a2'))
