"""
智能编排框架 - 动态监控和调整 (Monitoring & Adaptive Replanning)

实时执行监控与自适应重规划引擎。

设计文档: 02_智能编排框架设计.md
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from agent.core.types import (
    Anomaly,
    ExecutionMetrics,
    ExecutionPlan,
    ExecutionState,
)

logger = logging.getLogger(__name__)


class ExecutionMonitor:
    """实时执行监控。"""

    def monitor_execution(self, execution_state: ExecutionState) -> ExecutionMetrics:
        """监控执行进度和性能。"""
        metrics = ExecutionMetrics()

        total = len(execution_state.plan.all_tasks) if execution_state.plan else 0
        completed = len(execution_state.tasks_completed)

        metrics.overall_progress = (completed / total * 100) if total else 0.0
        metrics.critical_path_progress = self.calculate_critical_path_progress(execution_state)
        metrics.average_task_duration = self.calculate_avg_duration(execution_state.tasks_completed)
        metrics.parallelism_efficiency = self.calculate_parallelism_efficiency(execution_state)
        metrics.resource_utilization = self.get_resource_utilization()

        if execution_state.tasks_completed:
            metrics.success_rate = (
                len([t for t in execution_state.tasks_completed if t.success])
                / len(execution_state.tasks_completed)
                * 100
            )
        metrics.retry_rate = self.calculate_retry_rate(execution_state)
        metrics.bottleneck_tasks = self.identify_bottleneck_tasks(execution_state)
        metrics.estimated_remaining_time = self.estimate_remaining_time(execution_state)

        return metrics

    def calculate_critical_path_progress(self, state: ExecutionState) -> float:
        if not state.plan or not state.plan.execution_order:
            return 0.0
        total_levels = len(state.plan.execution_order)
        done = sum(
            1 for level in state.plan.execution_order
            if all(any(r.task_id == t.id and r.success for r in state.tasks_completed) for t in level)
        )
        return (done / total_levels * 100) if total_levels else 0.0

    @staticmethod
    def calculate_avg_duration(tasks: List[Any]) -> float:
        if not tasks:
            return 0.0
        return sum(getattr(t, "duration", 0.0) for t in tasks) / len(tasks)

    @staticmethod
    def calculate_parallelism_efficiency(state: ExecutionState) -> float:
        if not state.plan or not state.plan.execution_order:
            return 0.0
        max_width = max((len(level) for level in state.plan.execution_order), default=1)
        return min(1.0, len(state.tasks_completed) / max(1, max_width * len(state.plan.execution_order)))

    @staticmethod
    def get_resource_utilization() -> float:
        return 0.5

    @staticmethod
    def calculate_retry_rate(state: ExecutionState) -> float:
        return sum(state.retry_counts.values()) / max(1, len(state.tasks_completed) + len(state.tasks_failed))

    @staticmethod
    def identify_bottleneck_tasks(state: ExecutionState) -> List[str]:
        """识别瓶颈任务：耗时最长的任务。"""
        if not state.tasks_completed:
            return []
        slowest = sorted(state.tasks_completed, key=lambda t: getattr(t, "duration", 0.0), reverse=True)[0]
        return [slowest.task_id] if getattr(slowest, "duration", 0.0) > 30 else []

    def estimate_remaining_time(self, state: ExecutionState) -> float:
        if not state.plan or not state.plan.execution_order:
            return 0.0
        remaining_levels = max(0, len(state.plan.execution_order) - len(state.tasks_completed))
        return remaining_levels * self.calculate_avg_duration(state.tasks_completed) * 60

    def detect_anomalies(self, execution_state: ExecutionState) -> List[Anomaly]:
        """检测执行异常。"""
        anomalies: List[Anomaly] = []
        from datetime import datetime

        for task in execution_state.tasks_in_progress:
            elapsed = (datetime.now() - getattr(task, "start_time", datetime.now())).total_seconds()
            if elapsed > getattr(task, "timeout", 60.0) * 1.5:
                anomalies.append(
                    Anomaly(type="EXCESSIVE_TIMEOUT", task_id=task.id, severity="HIGH",
                            suggestion="Consider terminating and retrying")
                )

        recent_failure_rate = self._recent_failure_rate(execution_state, window=10)
        if recent_failure_rate > 0.3:
            anomalies.append(
                Anomaly(type="HIGH_FAILURE_RATE", severity="HIGH",
                        suggestion="Check system health and retry failed tasks")
            )
        return anomalies

    @staticmethod
    def _recent_failure_rate(state: ExecutionState, window: int = 10) -> float:
        recent = state.tasks_completed[-window:]
        if not recent:
            return 0.0
        return len([t for t in recent if not t.success]) / len(recent)


class AdaptiveReplanner:
    """自适应重规划引擎。"""

    async def replan_if_needed(self, execution_state: ExecutionState, current_metrics: ExecutionMetrics) -> Optional[ExecutionPlan]:
        """根据执行状态动态重规划。"""
        if not self.should_replan(execution_state, current_metrics):
            return None

        changes = self.identify_plan_changes(execution_state.plan, current_metrics)
        if not changes:
            return None

        new_plan = self.generate_revised_plan(execution_state.plan, execution_state.tasks_completed, changes)
        if self.is_plan_improvement(execution_state.plan, new_plan):
            return new_plan
        return None

    def should_replan(self, execution_state: ExecutionState, metrics: ExecutionMetrics) -> bool:
        """判断是否需要重规划。"""
        if metrics.retry_rate > 0.3:
            return True
        if metrics.bottleneck_tasks:
            return True
        if execution_state.plan and metrics.estimated_remaining_time > execution_state.plan.time_estimate * 2:
            return True
        return False

    @staticmethod
    def identify_plan_changes(plan: Optional[ExecutionPlan], metrics: ExecutionMetrics) -> List[str]:
        changes: List[str] = []
        if metrics.retry_rate > 0.3:
            changes.append("reduce_parallelism")
        if metrics.bottleneck_tasks:
            changes.append("split_bottleneck")
        return changes

    def generate_revised_plan(self, original: Optional[ExecutionPlan], completed: List[Any], changes: List[str]) -> Optional[ExecutionPlan]:
        if original is None:
            return None
        # 简化：复制原计划并降低并行度（将并行组展平为顺序）
        revised = ExecutionPlan(
            intent=original.intent,
            subtasks=original.subtasks,
            parallel_groups=original.parallel_groups,
            execution_order=original.execution_order,
            resource_estimate=original.resource_estimate,
            time_estimate=original.time_estimate,
        )
        if "reduce_parallelism" in changes:
            revised.execution_order = [[t] for group in original.execution_order for t in group]
        return revised

    @staticmethod
    def is_plan_improvement(original: Optional[ExecutionPlan], new: Optional[ExecutionPlan]) -> bool:
        return new is not None and original is not None


__all__ = ["ExecutionMonitor", "AdaptiveReplanner"]
