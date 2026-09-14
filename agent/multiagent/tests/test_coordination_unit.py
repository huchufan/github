import pytest

from agent.core.types import SubTaskResult, Task
from agent.multiagent.core.coordination import (ResultAggregator,
                                                TaskDecompositionCoordinator)


def test_decompose_parallel():
    coord = TaskDecompositionCoordinator()
    t = Task(task_id="t1", task_type="type")
    subs = coord._decompose_parallel(t)
    assert len(subs) == 3


def test_aggregate_merge():
    agg = ResultAggregator()
    r1 = SubTaskResult(task_id="t_s_1", status="SUCCESS", data={"a": 1, "b": 2})
    r2 = SubTaskResult(task_id="t_s_2", status="SUCCESS", data={"a": 1, "c": 3})
    merged = agg.merge_results([r1, r2])
    assert merged["a"] == 1
    assert "b" in merged and "c" in merged
