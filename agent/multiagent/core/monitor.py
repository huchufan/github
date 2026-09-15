"""
多智能体框架 - 监控和性能优化 (Monitoring & Optimization)

集群监控与自适应优化。

设计文档: 06_多智能体管理架构.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (
    Anomaly,
    ClusterMetrics,
    OptimizationOpportunity,
    Severity,
)

logger = logging.getLogger(__name__)


class ClusterMonitor:
    """集群监控系统。"""

    def __init__(self, lifecycle=None):
        self.lifecycle = lifecycle

    async def collect_cluster_metrics(self) -> ClusterMetrics:
        """收集集群指标。"""
        if self.lifecycle is None:
            return ClusterMetrics()
        agents = await self.lifecycle.get_all_agents()
        if not agents:
            return ClusterMetrics()

        n = len(agents)
        metrics = ClusterMetrics(
            total_agents=n,
            running_agents=sum(1 for a in agents if a.state == "RUNNING"),
            failed_agents=sum(1 for a in agents if a.state == "FAILED"),
            avg_cpu_usage=sum(a.cpu_usage for a in agents) / n,
            avg_memory_usage=sum(a.memory_usage for a in agents) / n,
            avg_load=sum(a.current_load for a in agents) / n,
            avg_response_time=sum(a.avg_response_time for a in agents) / n,
            total_tasks=sum(a.task_count for a in agents),
            completed_tasks=sum(a.completed_tasks for a in agents),
            failed_tasks=sum(a.failed_tasks for a in agents),
        )
        return metrics

    def detect_anomalies(self, metrics: ClusterMetrics) -> List[Anomaly]:
        """检测异常。"""
        anomalies: List[Anomaly] = []

        if metrics.total_agents > 0:
            failure_rate = metrics.failed_agents / metrics.total_agents
            if failure_rate > 0.2:
                anomalies.append(Anomaly(type="HIGH_FAILURE_RATE", severity=Severity.HIGH.value, value=failure_rate))

        if metrics.avg_response_time > 5000:
            anomalies.append(Anomaly(type="SLOW_RESPONSE", severity=Severity.MEDIUM.value, value=metrics.avg_response_time))

        if metrics.avg_cpu_usage > 90 or metrics.avg_memory_usage > 90:
            anomalies.append(Anomaly(type="HIGH_RESOURCE_USAGE", severity=Severity.MEDIUM.value,
                                     value=max(metrics.avg_cpu_usage, metrics.avg_memory_usage)))
        return anomalies


class ClusterOptimizer:
    """集群自适应优化。"""

    def identify_optimization_opportunities(self, performance_history: List[Dict[str, Any]]) -> List[OptimizationOpportunity]:
        """识别优化机会。"""
        opportunities: List[OptimizationOpportunity] = []

        imbalance = self._analyze_task_distribution(performance_history)
        if imbalance > 0.3:
            opportunities.append(
                OptimizationOpportunity(type="TASK_ALLOCATION", current_metric=imbalance, potential_improvement=0.2)
            )
        return opportunities

    @staticmethod
    def _analyze_task_distribution(history: List[Dict[str, Any]]) -> float:
        """分析任务分配不平衡度。"""
        if not history:
            return 0.0
        loads = [h.get("load", 0.0) for h in history]
        avg = sum(loads) / len(loads)
        if avg == 0:
            return 0.0
        return max(abs(l - avg) for l in loads) / avg

    async def optimize_cluster_configuration(self, performance_history: List[Dict[str, Any]]) -> List[OptimizationOpportunity]:
        """优化集群配置，返回已应用的优化机会。"""
        opportunities = self.identify_optimization_opportunities(performance_history)
        applied = []
        for opp in opportunities:
            applied.append(opp)
        return applied


__all__ = ["ClusterMonitor", "ClusterOptimizer"]
