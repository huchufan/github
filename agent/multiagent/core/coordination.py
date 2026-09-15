"""
多智能体框架 - 协作和竞争 (Collaboration & Competition)

任务分解、子任务分配、结果融合与冲突解决。

设计文档: 06_多智能体管理架构.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import SubTaskResult, Task, TaskCoordination

logger = logging.getLogger(__name__)


class TaskDecompositionCoordinator:
    """任务分解和子任务分配。"""

    def __init__(self, distributor=None):
        self.distributor = distributor

    async def decompose_task(self, task: Task) -> List[Task]:
        """分解任务为子任务。"""
        strategy = task.decomposition_strategy
        if strategy == "PARALLEL":
            return self._decompose_parallel(task)
        if strategy == "HIERARCHICAL":
            return self._decompose_hierarchical(task)
        # SEQUENTIAL 或 ADAPTIVE 默认顺序分解
        return self._decompose_sequential(task)

    def _decompose_sequential(self, task: Task) -> List[Task]:
        return [self._make_subtask(task, 0)]

    def _decompose_parallel(self, task: Task) -> List[Task]:
        # 并行分解为 3 个独立子任务
        return [self._make_subtask(task, i) for i in range(3)]

    def _decompose_hierarchical(self, task: Task) -> List[Task]:
        parent = self._make_subtask(task, 0)
        children = [self._make_subtask(task, i) for i in range(1, 3)]
        return [parent] + children

    @staticmethod
    def _make_subtask(task: Task, index: int) -> Task:
        return Task(
            task_id=f"{task.task_id}_sub_{index}",
            task_type=task.task_type,
            parameters=task.parameters,
            priority=task.priority,
            required_skills=task.required_skills,
            estimated_resources=task.estimated_resources,
        )

    async def decompose_and_assign(self, task: Task) -> Dict[str, Any]:
        """分解复杂任务并分配子任务。"""
        subtasks = await self.decompose_task(task)
        coordination = TaskCoordination(parent_task_id=task.task_id, subtasks=subtasks)

        if self.distributor is None:
            return {"coordination": coordination, "results": []}

        for subtask in subtasks:
            agent_id = await self.distributor.distribute_task(subtask)
            if agent_id:
                coordination.assigned_agents[subtask.task_id] = agent_id

        return {
            "coordination": coordination,
            "assigned": len(coordination.assigned_agents),
        }


class ResultAggregator:
    """结果融合和冲突解决。"""

    async def aggregate_results(
        self, subtask_results: List[SubTaskResult], aggregation_strategy: str
    ) -> Any:
        """聚合子任务结果。"""
        if aggregation_strategy == "MERGE":
            return self.merge_results(subtask_results)
        if aggregation_strategy == "VOTING":
            return self.voting_results(subtask_results)
        if aggregation_strategy == "WEIGHTED":
            return self.weighted_fusion(subtask_results)
        raise ValueError(f"Unknown aggregation strategy: {aggregation_strategy}")

    def merge_results(self, results: List[SubTaskResult]) -> Dict[str, Any]:
        """合并结果。"""
        merged: Dict[str, Any] = {}
        for result in results:
            if result.status == "SUCCESS" and isinstance(result.data, dict):
                conflicts = self.detect_conflicts(merged, result.data)
                if conflicts:
                    merged = self.resolve_conflicts(merged, result.data, conflicts)
                else:
                    merged.update(result.data)
        return merged

    @staticmethod
    def voting_results(results: List[SubTaskResult]) -> Any:
        """投票策略：多数决定。"""
        from collections import Counter

        values = [r.data for r in results if r.status == "SUCCESS"]
        if not values:
            return None
        # 对可哈希值投票
        try:
            return Counter(values).most_common(1)[0][0]
        except TypeError:
            return values[0]

    @staticmethod
    def weighted_fusion(results: List[SubTaskResult]) -> Dict[str, Any]:
        """加权融合。"""
        fused: Dict[str, Any] = {}
        for result in results:
            if result.status == "SUCCESS" and isinstance(result.data, dict):
                for key, value in result.data.items():
                    if isinstance(value, (int, float)):
                        fused[key] = fused.get(key, 0) + value / max(len(results), 1)
                    else:
                        fused[key] = value
        return fused

    @staticmethod
    def detect_conflicts(current: Dict, new: Dict) -> List[str]:
        """检测冲突。"""
        return [key for key in current if key in new and current[key] != new[key]]

    @staticmethod
    def resolve_conflicts(current: Dict, new: Dict, conflicts: List[str]) -> Dict:
        """解决冲突。"""
        resolution = current.copy()
        for key in conflicts:
            if isinstance(current[key], (int, float)):
                resolution[key] = (current[key] + new[key]) / 2
            elif isinstance(current[key], list):
                resolution[key] = list(set(current[key] + new[key]))
            else:
                resolution[key] = current[key]
        return resolution


__all__ = ["TaskDecompositionCoordinator", "ResultAggregator"]
