import asyncio

import pytest

from agent.core.types import SubTask
from agent.orchestration.core.executor import (ErrorHandlingStrategy,
                                               OrchestrationEngine)


def dummy_skill(params, ctx=None):
    return {"ok": True}


async def async_dummy(params, ctx=None):
    return {"ok": True}


def test_execute_single_task_sync():
    engine = OrchestrationEngine(skill_registry={"s1": dummy_skill})
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sub = SubTask(id="t1", skill_name="s1", parameters={})
    res = loop.run_until_complete(engine.execute_single_task(sub, None, None))
    assert res.success


def test_error_handling_retry():
    engine = OrchestrationEngine(
        skill_registry={"sbad": lambda p, c: (_ for _ in ()).throw(Exception("fail"))}
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sub = SubTask(id="t_err", skill_name="sbad", parameters={}, timeout=1)
    res = loop.run_until_complete(engine.execute_single_task(sub, None, None))
    assert not res.success
