"""
智能编排框架 - 任务规划和分解 (Task Planning)

将意图分解为子任务、分析依赖、构建 DAG 并生成执行计划。

设计文档: 02_智能编排框架设计.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (
    ExecutionPlan,
    Intent,
    ParameterSet,
    SubTask,
)
from agent.orchestration.core.dag import DAG, Node

logger = logging.getLogger(__name__)


class TaskPlanner:
    """任务规划和分解。"""

    def plan_execution(
        self,
        intent: Intent,
        parameters: ParameterSet,
        context: Any = None,
    ) -> ExecutionPlan:
        """生成执行计划。"""
        # 步骤 1: 识别需要的技能
        required_skills = self.identify_required_skills(intent)

        # 步骤 2: 分解任务为子任务
        subtasks = self.decompose_into_subtasks(intent, required_skills, parameters)

        # 步骤 3: 分析依赖关系
        dependencies = self.analyze_dependencies(subtasks)

        # 步骤 4: 构建 DAG
        dag = self.build_dag(subtasks, dependencies)

        # 步骤 5: 优化排序（分层执行顺序）
        execution_order = dag.get_execution_order()

        # 步骤 6: 并行化分组
        parallel_groups = self.identify_parallelizable_groups(subtasks, execution_order)

        # 步骤 7: 资源与时间估计
        resource_estimate = self.estimate_resources(parallel_groups)
        time_estimate = self.estimate_execution_time(parallel_groups)

        # 步骤 8: 生成执行计划
        return ExecutionPlan(
            intent=intent,
            subtasks=subtasks,
            parallel_groups=parallel_groups,
            execution_order=self._to_task_groups(execution_order, subtasks),
            resource_estimate=resource_estimate,
            time_estimate=time_estimate,
            fallback_strategies=self.generate_fallback_strategies(subtasks),
            contingency_plans=self.generate_contingency_plans(subtasks),
        )

    def identify_required_skills(self, intent: Intent) -> List[str]:
        """识别意图所需的技能。"""
        return list(intent.skills_involved)

    def decompose_into_subtasks(
        self,
        intent: Intent,
        required_skills: List[str],
        parameters: ParameterSet,
    ) -> List[SubTask]:
        """将意图分解为子任务（按技能线性化，可被并行策略覆盖）。"""
        subtasks: List[SubTask] = []
        for idx, skill in enumerate(required_skills):
            subtask = SubTask(
                id=f"{intent.name}_task_{idx}",
                skill_name=skill,
                description=f"Execute {skill}",
                depends_on=[f"{intent.name}_task_{idx - 1}"] if idx > 0 else [],
                parameters=dict(parameters.parameters),
            )
            subtasks.append(subtask)
        return subtasks

    def analyze_dependencies(self, subtasks: List[SubTask]) -> Dict[str, List[str]]:
        """分析依赖关系，返回 task_id -> 依赖列表。"""
        return {t.id: list(t.depends_on) for t in subtasks}

    def build_dag(self, subtasks: List[SubTask], dependencies: Dict[str, List[str]]) -> DAG:
        """构建有向无环图。"""
        dag = DAG()
        for t in subtasks:
            dag.add_node(Node(id=t.id, name=t.skill_name, task_type=t.skill_name, params=t.parameters))
        for task_id, deps in dependencies.items():
            for dep in deps:
                dag.add_edge(dep, task_id)
        return dag

    def identify_parallelizable_groups(
        self,
        subtasks: List[SubTask],
        execution_order: List[List[str]],
    ) -> List[List[SubTask]]:
        """识别可并行执行的任务组。"""
        task_map = {t.id: t for t in subtasks}
        groups: List[List[SubTask]] = []
        for level_ids in execution_order:
            level_tasks = [task_map[i] for i in level_ids if i in task_map]
            if level_tasks:
                groups.append(level_tasks)
        return groups

    @staticmethod
    def _to_task_groups(execution_order: List[List[str]], subtasks: List[SubTask]) -> List[List[SubTask]]:
        task_map = {t.id: t for t in subtasks}
        return [[task_map[i] for i in level_ids if i in task_map] for level_ids in execution_order]

    def estimate_resources(self, parallel_groups: List[List[SubTask]]) -> Dict[str, Any]:
        """估计资源需求。"""
        total = sum(len(g) for g in parallel_groups)
        return {
            "total_tasks": total,
            "max_parallelism": max((len(g) for g in parallel_groups), default=1),
            "estimated_memory": total * 0.1,
            "estimated_cpu": total * 0.05,
        }

    def estimate_execution_time(self, parallel_groups: List[List[SubTask]]) -> float:
        """估计执行时间（每层 60s 基准）。"""
        return len(parallel_groups) * 60.0

    def generate_fallback_strategies(self, subtasks: List[SubTask]) -> List[Any]:
        return [{"task_id": t.id, "strategy": "retry_on_transient"} for t in subtasks]

    def generate_contingency_plans(self, subtasks: List[SubTask]) -> List[Any]:
        return [{"task_id": t.id, "plan": "skip_and_notify"} for t in subtasks]


__all__ = ["TaskPlanner"]
