import asyncio
from agent.orchestration.core.executor import OrchestrationEngine
from agent.core.types import SubTask, ExecutionPlan, TaskResult, OperationStatus


def sync_ok(params, ctx=None):
    return {"ok": True}


def sync_fail(params, ctx=None):
    raise RuntimeError('boom')


def test_handle_task_failures_retry_exhausted_to_stop():
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
    res = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert res is False


def test_handle_task_failures_fallback_no_skill_stops():
    # when fallback action has no fallback_skill -> should STOP
    engine = OrchestrationEngine(skill_registry={'bad': sync_fail})
    task = SubTask(id='t_fb2', skill_name='bad', retry_policy='execute_fallback')
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(task_id='t_fb2', status=OperationStatus.FAILURE.value, success=False, error='fail')
    state = type('S', (), {'tasks_failed': [], 'tasks_completed': [], 'retry_counts': {}, 'get_retry_count': lambda self, x: 0})()
    # ensure fallback has no skill
    engine.error_strategy.strategies['execute_fallback']['fallback_skill'] = None
    res = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert res is False


def test_handle_task_failures_continue_true():
    engine = OrchestrationEngine(skill_registry={'bad': sync_fail})
    task = SubTask(id='t_c', skill_name='bad', retry_policy='skip_and_continue')
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(task_id='t_c', status=OperationStatus.FAILURE.value, success=False, error='err')
    state = type('S', (), {'tasks_failed': [], 'tasks_completed': [], 'retry_counts': {}, 'get_retry_count': lambda self, x: 0})()
    res = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert res is True
