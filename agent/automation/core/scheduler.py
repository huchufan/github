"""
自动化执行框架 - 调度引擎 (Scheduling Engine)

智能调度引擎：优先级队列、资源感知调度。

设计文档: 04_自动化执行框架.md
"""

from __future__ import annotations

import asyncio
import heapq
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from agent.core.types import (
    JobResult,
    OperationStatus,
    ResourceSnapshot,
    ScheduleJob,
    Workflow,
)
from agent.core.errors import WorkflowNotFoundError

logger = logging.getLogger(__name__)


class PriorityQueue:
    """优先级队列（值越大优先级越高）。"""

    def __init__(self):
        self._heap: List[Tuple[float, int, Any]] = []
        self._counter = 0

    def put(self, item: Any, priority: float = 0.0) -> None:
        heapq.heappush(self._heap, (-priority, self._counter, item))
        self._counter += 1

    def get(self) -> Optional[Any]:
        if not self._heap:
            return None
        return heapq.heappop(self._heap)[2]

    def __len__(self) -> int:
        return len(self._heap)

    def peek_priority(self) -> float:
        if not self._heap:
            return 0.0
        return -self._heap[0][0]


class SchedulingEngine:
    """智能调度引擎。"""

    def __init__(self, max_workers: int = 10):
        self.job_queue = PriorityQueue()
        self.max_workers = max_workers
        self.workflow_registry: Dict[str, Workflow] = {}
        self._running: Dict[str, ScheduleJob] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        self.workflow_registry[workflow.id] = workflow

    def get_workflow(self, workflow_id: str) -> Workflow:
        if workflow_id not in self.workflow_registry:
            raise WorkflowNotFoundError(workflow_id)
        return self.workflow_registry[workflow_id]

    async def schedule_workflow(self, workflow: Workflow, trigger: Any = None, execution_time: Optional[datetime] = None) -> ScheduleJob:
        """调度工作流执行。"""
        scheduled = execution_time or datetime.now(timezone.utc)
        priority = self.calculate_priority(workflow, trigger)
        estimate = self.estimate_resource_requirement(workflow)

        job = ScheduleJob(
            workflow_id=workflow.id,
            trigger_id=getattr(trigger, "trigger_id", ""),
            scheduled_time=scheduled,
            priority=priority,
            estimated_duration=estimate["duration"],
            estimated_memory=estimate["memory"],
            estimated_cpu=estimate["cpu"],
            max_retries=workflow.max_retries,
            timeout=workflow.timeout,
            retries_remaining=workflow.max_retries,
        )
        self.job_queue.put(job, priority=priority)
        return job

    @staticmethod
    def calculate_priority(workflow: Workflow, trigger: Any = None) -> int:
        return workflow.priority

    @staticmethod
    def estimate_resource_requirement(workflow: Workflow) -> Dict[str, float]:
        return {
            "duration": workflow.timeout / 10,
            "memory": workflow.memory_requirement,
            "cpu": workflow.cpu_requirement,
        }

    def can_execute_immediately(self, job: ScheduleJob) -> bool:
        return len(self._running) < self.max_workers

    async def execute_job(self, job: ScheduleJob, run_fn=None) -> JobResult:
        """执行单个调度任务。"""
        job.status = OperationStatus.RUNNING.value
        job.started_at = datetime.now()
        start = job.started_at

        try:
            if run_fn is None:
                result = await asyncio.sleep(0)  # 无执行函数时仅标记成功
                data = {"workflow_id": job.workflow_id}
            else:
                data = await run_fn(job)

            job.status = OperationStatus.SUCCESS.value
            return JobResult(job_id=job.job_id, status=OperationStatus.SUCCESS.value, result=data,
                             duration=(datetime.now() - start).total_seconds())
        except asyncio.TimeoutError:
            job.status = OperationStatus.TIMEOUT.value
            return JobResult(job_id=job.job_id, status=OperationStatus.TIMEOUT.value,
                             error="Job execution exceeded timeout")
        except Exception as exc:
            if job.retries_remaining > 0:
                job.retries_remaining -= 1
                job.status = OperationStatus.SCHEDULED.value
                self.job_queue.put(job, priority=job.priority)
                return JobResult(job_id=job.job_id, status=OperationStatus.RETRY.value, error=str(exc),
                                 retries_remaining=job.retries_remaining)
            job.status = OperationStatus.FAILURE.value
            return JobResult(job_id=job.job_id, status=OperationStatus.FAILURE.value, error=str(exc))


class ResourceAwareScheduler:
    """资源感知调度器。"""

    def calculate_scheduling_score(self, job: ScheduleJob, current_resources: ResourceSnapshot) -> float:
        """计算任务的调度分数。"""
        score = 0.0
        # 因子 1: 优先级（40%）
        score += (job.priority / 100.0) * 0.4
        # 因子 2: 等待时间（30%）
        wait = (datetime.now(timezone.utc) - job.created_at).total_seconds()
        score += min(wait / 3600, 1.0) * 0.3
        # 因子 3: 资源可用性（20%）
        score += self.calculate_resource_availability(job.estimated_memory, job.estimated_cpu, current_resources) * 0.2
        # 因子 4: SLA 风险（10%）
        score += self.calculate_sla_risk(job) * 0.1
        return score

    @staticmethod
    def calculate_resource_availability(est_memory: float, est_cpu: float, resources: ResourceSnapshot) -> float:
        mem_ok = resources.memory >= est_memory
        cpu_ok = resources.cpu >= est_cpu
        return 1.0 if (mem_ok and cpu_ok) else 0.5

    @staticmethod
    def calculate_sla_risk(job: ScheduleJob) -> float:
        # 等待越久风险越低（紧迫性越高）
        wait = (datetime.now(timezone.utc) - job.created_at).total_seconds()
        return min(wait / 3600, 1.0)

    def optimize_scheduling_order(self, pending_jobs: List[ScheduleJob], current_resources: ResourceSnapshot) -> List[ScheduleJob]:
        """优化调度顺序。"""
        scored = [(job, self.calculate_scheduling_score(job, current_resources)) for job in pending_jobs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [job for job, _ in scored]


__all__ = ["PriorityQueue", "SchedulingEngine", "ResourceAwareScheduler"]
