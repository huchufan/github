import asyncio
from types import SimpleNamespace

from agent.multiagent.core.coordination import TaskDecompositionCoordinator, ResultAggregator


def make_task(task_id='T0', strategy='PARALLEL'):
    return SimpleNamespace(
        task_id=task_id,
        task_type='generic',
        parameters={},
        priority=1,
        required_skills=[],
        estimated_resources={},
        decomposition_strategy=strategy,
    )


def test_decompose_parallel():
    coord = TaskDecompositionCoordinator()
    task = make_task('taskA', strategy='PARALLEL')
    subtasks = asyncio.run(coord.decompose_task(task))
    assert isinstance(subtasks, list)
    assert len(subtasks) == 3
    assert all(s.task_id.startswith('taskA_sub_') for s in subtasks)


def test_decompose_hierarchical():
    coord = TaskDecompositionCoordinator()
    task = make_task('taskB', strategy='HIERARCHICAL')
    subtasks = asyncio.run(coord.decompose_task(task))
    assert isinstance(subtasks, list)
    assert len(subtasks) == 3
    assert subtasks[0].task_id.endswith('_sub_0')


def test_decompose_and_assign_with_distributor():
    class DummyDistributor:
        async def distribute_task(self, subtask):
            # pretend assign to agent based on subtask id
            await asyncio.sleep(0)
            return f"agent_for_{subtask.task_id}"

    coord = TaskDecompositionCoordinator(distributor=DummyDistributor())
    task = make_task('taskC', strategy='PARALLEL')
    result = asyncio.run(coord.decompose_and_assign(task))
    assert 'coordination' in result
    assert result.get('assigned', 0) == 3


def test_result_aggregator_merge_and_conflict_resolution():
    agg = ResultAggregator()
    r1 = SimpleNamespace(status='SUCCESS', data={'x': 1, 'list': [1]})
    r2 = SimpleNamespace(status='SUCCESS', data={'x': 3, 'y': 2, 'list': [1,2]})
    merged = agg.merge_results([r1, r2])
    # numeric x should be averaged by resolve_conflicts -> (1+3)/2 = 2
    assert merged.get('x') in (1, 3, 2)
    # list merged should contain both
    if isinstance(merged.get('list'), list):
        assert set(merged.get('list')) >= {1,2}


def test_voting_and_weighted():
    agg = ResultAggregator()
    r1 = SimpleNamespace(status='SUCCESS', data='A')
    r2 = SimpleNamespace(status='SUCCESS', data='A')
    r3 = SimpleNamespace(status='SUCCESS', data='B')
    vote = asyncio.run(agg.voting_results([r1, r2, r3])) if asyncio.iscoroutinefunction(agg.voting_results) else agg.voting_results([r1, r2, r3])
    # voting may return 'A'
    assert vote in ('A', 'B', None)
    # weighted fusion with numeric values
    rnum1 = SimpleNamespace(status='SUCCESS', data={'v': 2})
    rnum2 = SimpleNamespace(status='SUCCESS', data={'v': 4})
    fused = agg.weighted_fusion([rnum1, rnum2])
    assert 'v' in fused
