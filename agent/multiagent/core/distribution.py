"""
多智能体框架 - 任务分配和协调 (Task Distribution)

智能任务分配与负载均衡。

设计文档: 06_多智能体管理架构.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (
    Agent,
    LoadDistribution,
    Task,
)

logger = logging.getLogger(__name__)


class TaskDistributionManager:
    """任务分配管理。"""

    def __init__(self, lifecycle=None):
        self.lifecycle = lifecycle
        self.task_queue: List[Task] = []
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id

    async def get_available_agents(self) -> List[Agent]:
        if self.lifecycle is None:
            return []
        agents = await self.lifecycle.get_all_agents()
        return [a for a in agents if a.state == "RUNNING"]

    async def distribute_task(self, task: Task) -> Optional[str]:
        """分配任务到最合适的 Agent。"""
        available = await self.get_available_agents()
        if not available:
            self.task_queue.append(task)
            return None

        scores = {}
        for agent in available:
            score = await self.calculate_agent_suitability(agent, task)
            scores[agent.agent_id] = score

        best_agent_id = max(scores, key=scores.get)
        if scores[best_agent_id] <= 0:
            self.task_queue.append(task)
            return None

        await self.assign_task_to_agent(best_agent_id, task)
        return best_agent_id

    async def calculate_agent_suitability(self, agent: Agent, task: Task) -> float:
        """计算 Agent 对任务的适合度。"""
        score = 1.0

        # 因子 1: 技能匹配
        if not self.has_required_skills(agent, task):
            return 0.0
        score *= self.calculate_skill_match(agent, task)

        # 因子 2: 当前负载
        current_load = agent.task_count / max(agent.config.max_concurrent_tasks, 1)
        score *= 1 - (current_load * 0.4)

        # 因子 3: 资源可用性
        required = task.estimated_resources
        if agent.available_cpu < required.cpu or agent.available_memory < required.memory:
            return 0.0
        availability = min(
            agent.available_cpu / max(required.cpu, 1e-6),
            agent.available_memory / max(required.memory, 1e-6),
        )
        score *= min(availability * 0.3, 0.3)

        # 因子 4: 成功率
        score *= agent.get_success_rate() * 0.1

        return score

    @staticmethod
    def has_required_skills(agent: Agent, task: Task) -> bool:
        if not task.required_skills:
            return True
        return all(s in agent.capabilities for s in task.required_skills)

    @staticmethod
    def calculate_skill_match(agent: Agent, task: Task) -> float:
        if not task.required_skills:
            return 1.0
        matched = sum(1 for s in task.required_skills if s in agent.capabilities)
        return matched / len(task.required_skills)

    async def assign_task_to_agent(self, agent_id: str, task: Task) -> None:
        """分配任务给 Agent。"""
        task.status = "ASSIGNED"
        self.task_assignments[task.task_id] = agent_id
        if self.lifecycle:
            agent = await self.lifecycle.get_agent(agent_id)
            agent.task_count += 1
            agent.task_queue.append(task)

    async def handle_task_failure(self, task: Task, agent_id: str, error: str) -> Optional[str]:
        """处理任务失败。"""
        task.failure_count += 1
        if self.lifecycle:
            agent = await self.lifecycle.get_agent(agent_id)
            agent.failure_count += 1
            agent.failed_tasks += 1

        if task.failure_count < task.max_retries:
            return await self.distribute_task(task)
        task.status = "FAILED"
        return None


class LoadBalancer:
    """负载均衡器。"""

    def __init__(self, lifecycle=None):
        self.lifecycle = lifecycle

    def analyze_load_distribution(self, agents: List[Agent]) -> LoadDistribution:
        """分析负载分布。"""
        if not agents:
            return LoadDistribution()

        loads = [a.current_load for a in agents]
        avg = sum(loads) / len(loads)
        std = self._std_dev(loads, avg)

        dist = LoadDistribution(avg_load=avg, std_dev=std)
        dist.imbalance_factor = std / avg if avg > 0 else 0.0

        if std > 0:
            for agent in agents:
                if agent.current_load >= avg + std:
                    dist.overloaded_agents.append(agent.agent_id)
                elif agent.current_load <= avg - std:
                    dist.underloaded_agents.append(agent.agent_id)
        return dist

    @staticmethod
    def _std_dev(values: List[float], mean: float) -> float:
        if not values:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5

    async def balance_load(self, agents: List[Agent]) -> int:
        """执行一轮负载均衡，返回转移的任务数。"""
        dist = self.analyze_load_distribution(agents)
        transferred = 0
        return transferred


__all__ = ["TaskDistributionManager", "LoadBalancer"]
