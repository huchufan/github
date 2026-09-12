import asyncio
from agent.orchestration.core.executor import OrchestrationEngine, ErrorHandlingStrategy
from agent.core.types import SubTask, ExecutionPlan, TaskResult, OperationStatus


def sync_ok(params, ctx=None):
    return {"ok": True}


def sync_fail(params, ctx=None):
    raise RuntimeError('boom')


def test_orchestrate_execution_success():
    engine = OrchestrationEngine(skill_registry={'s1': sync_ok, 's2': sync_ok})
    t1 = SubTask(id='t1', skill_name='s1')
    t2 = SubTask(id='t2', skill_name='s2')
    plan = ExecutionPlan(subtasks=[t1, t2], execution_order=[[t1, t2]])
    res = asyncio.run(engine.orchestrate_execution(plan, None))
    assert res.status == OperationStatus.SUCCESS.value
    assert res.tasks_executed == 2


def test_orchestrate_execution_abort_on_immediate_fail():
    engine = OrchestrationEngine(skill_registry={'bad': sync_fail})
    t = SubTask(id='t_bad', skill_name='bad', retry_policy='immediate_fail')
    plan = ExecutionPlan(subtasks=[t], execution_order=[[t]])
    res = asyncio.run(engine.orchestrate_execution(plan, None))
    assert res.status == OperationStatus.FAILURE.value
    assert res.tasks_failed >= 1


def test_execute_task_group_exception_mapping():
    # subclass engine to force execute_single_task to raise for one task
    class BorkEngine(OrchestrationEngine):
        async def execute_single_task(self, subtask, state, context):
            if subtask.id == 'explode':
                raise RuntimeError('explode')
            return await super().execute_single_task(subtask, state, context)

    engine = BorkEngine(skill_registry={'ok': sync_ok})
    t1 = SubTask(id='explode', skill_name='ok')
    t2 = SubTask(id='tok', skill_name='ok')
    results = asyncio.run(engine.execute_task_group([t1, t2], type('S', (), {'tasks_failed': [], 'tasks_completed': [], 'retry_counts': {}, 'get_retry_count': lambda self, x: 0})(), None))
    # ensure exception was converted to TaskResult for 'explode'
    ids = [r.task_id for r in results]
    assert 'explode' in ids and 'tok' in ids


def test_handle_task_failures_retry_exhausted_stops():
    engine = OrchestrationEngine(skill_registry={'bad': sync_fail})
    task = SubTask(id='t_stop', skill_name='bad', retry_policy='retry_on_transient')
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(task_id='t_stop', status=OperationStatus.FAILURE.value, success=False, error='fatal')
    class S:
        tasks_failed = []
        tasks_completed = []
        retry_counts = {'t_stop': 3}
        def get_retry_count(self, _):
            return self.retry_counts.get('t_stop', 0)
    state = S()
    should_continue = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert should_continue is False
