import asyncio
from agent.orchestration.core.executor import OrchestrationEngine, ErrorHandlingStrategy
from agent.core.types import SubTask, ExecutionPlan, TaskResult, OperationStatus


def flaky_once_then_ok(params, ctx=None):
    if not hasattr(flaky_once_then_ok, 'called'):
        flaky_once_then_ok.called = True
        raise RuntimeError('transient')
    return {'ok': True}


def always_fail(params, ctx=None):
    raise RuntimeError('fatal')


def test_handle_task_failures_retry_path():
    engine = OrchestrationEngine(skill_registry={'once': flaky_once_then_ok})
    task = SubTask(id='t_retry', skill_name='once', retry_policy='retry_on_transient')
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(task_id='t_retry', status=OperationStatus.FAILURE.value, success=False, error='transient')
    state = type('S', (), {'tasks_failed': [], 'tasks_completed': [], 'retry_counts': {}, 'get_retry_count': lambda self, x: self.retry_counts.get(x, 0)})()
    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    # should attempt retry; either succeed and be in tasks_completed or be recorded in tasks_failed
    assert cont is True
    assert len(state.tasks_completed) + len(state.tasks_failed) >= 1


def test_handle_task_failures_fallback_path():
    engine = OrchestrationEngine(skill_registry={'orig': always_fail, 'alt': lambda p, c: {'ok': True}})
    # set task to use execute_fallback strategy
    task = SubTask(id='t_fb', skill_name='orig', retry_policy='execute_fallback')
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(task_id='t_fb', status=OperationStatus.FAILURE.value, success=False, error='fatal')
    state = type('S', (), {'tasks_failed': [], 'tasks_completed': [], 'retry_counts': {}, 'get_retry_count': lambda self, x: self.retry_counts.get(x, 0)})()
    # force fallback to use 'alt' and allow one retry so fallback path is taken
    engine.error_strategy.strategies['execute_fallback']['fallback_skill'] = 'alt'
    engine.error_strategy.strategies['execute_fallback']['retries'] = 1
    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    assert cont is True
    # fallback should have been attempted and produced at least one completed record
    assert len(state.tasks_completed) >= 1


def test_handle_task_failures_continue_path():
    engine = OrchestrationEngine(skill_registry={'bad': always_fail})
    # make a task whose strategy is skip_and_continue
    task = SubTask(id='t_cont', skill_name='bad', retry_policy='skip_and_continue')
    plan = ExecutionPlan(subtasks=[task])
    failed = TaskResult(task_id='t_cont', status=OperationStatus.FAILURE.value, success=False, error='fatal')
    state = type('S', (), {'tasks_failed': [], 'tasks_completed': [], 'retry_counts': {}, 'get_retry_count': lambda self, x: self.retry_counts.get(x, 0)})()
    cont = asyncio.run(engine.handle_task_failures([failed], state, plan))
    # continue strategy should not stop overall execution
    assert cont is True

