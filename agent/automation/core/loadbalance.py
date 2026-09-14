"""
自动化执行框架 - 负载均衡和故障转移 (Load Balancing & Failover)

工作流到工作进程的智能分配与故障转移。

设计文档: 04_自动化执行框架.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.errors import NoAvailableWorkersError
from agent.core.types import Worker, Workflow

logger = logging.getLogger(__name__)


class LoadBalancingManager:
    """负载均衡和故障转移。"""

    def __init__(self):
        self.workers: List[Worker] = []
        self._assignments: Dict[str, str] = {}  # workflow_id -> worker_id

    def register_worker(self, worker: Worker) -> None:
        self.workers.append(worker)

    def get_available_workers(self, exclude: Optional[Worker] = None) -> List[Worker]:
        return [w for w in self.workers if w.status == "healthy" and w is not exclude]

    async def distribute_workflow_execution(
        self, workflow: Workflow, available_workers: List[Worker]
    ) -> Worker:
        """分配工作流到最合适的工作进程。"""
        if not available_workers:
            raise NoAvailableWorkersError()
        scored = [
            (w, self.evaluate_worker_suitability(w, workflow))
            for w in available_workers
        ]
        selected = max(scored, key=lambda x: x[1])[0]
        self._assignments[workflow.id] = selected.worker_id
        return selected

    def evaluate_worker_suitability(self, worker: Worker, workflow: Workflow) -> float:
        """评估工作进程的适合度。"""
        score = 1.0

        if worker.available_memory < workflow.memory_requirement:
            score -= 0.5
        if worker.available_cpu < workflow.cpu_requirement:
            score -= 0.3

        load_factor = worker.current_load / max(worker.max_capacity, 1e-6)
        score *= 1 - load_factor * 0.5

        if worker.status != "healthy":
            score -= 0.2

        if worker.has_required_tools(workflow):
            score += 0.2

        return max(score, 0.0)

    async def handle_worker_failure(
        self, failed_worker: Worker, workflow: Workflow
    ) -> Worker:
        """处理工作进程失败并转移到备用进程。"""
        backup = self.get_available_workers(exclude=failed_worker)
        if not backup:
            raise NoAvailableWorkersError()
        return await self.distribute_workflow_execution(workflow, backup)


__all__ = ["LoadBalancingManager"]
