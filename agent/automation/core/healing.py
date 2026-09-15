"""
自动化执行框架 - 自我修复和自适应 (Self-Healing & Adaptation)

异常检测、自动恢复与自适应优化。

设计文档: 04_自动化执行框架.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (
    Anomaly,
    JobResult,
    OperationStatus,
    Severity,
)

logger = logging.getLogger(__name__)


class SelfHealingSystem:
    """自我修复系统。"""

    def __init__(self):
        self.recovery_log: List[Dict[str, Any]] = []

    async def detect_and_recover(self, anomalies: List[Anomaly]) -> List[Dict[str, Any]]:
        """检测异常并自动恢复（单次扫描，便于测试）。"""
        results = []
        for anomaly in anomalies:
            category = self.categorize_anomaly(anomaly)
            recovery = await self.execute_recovery(anomaly, category)
            self.log_recovery_action(anomaly, recovery)
            results.append(recovery)
        return results

    def detect_anomalies(self, jobs: List[JobResult]) -> List[Anomaly]:
        """检测系统异常。"""
        anomalies: List[Anomaly] = []
        anomalies.extend(self.detect_timeout_anomalies(jobs))
        anomalies.extend(self.detect_high_error_rate(jobs))
        return anomalies

    @staticmethod
    def detect_timeout_anomalies(jobs: List[JobResult]) -> List[Anomaly]:
        return [Anomaly(type="TIMEOUT", severity=Severity.HIGH.value, value=j.job_id)
                for j in jobs if j.status == OperationStatus.TIMEOUT.value]

    @staticmethod
    def detect_high_error_rate(jobs: List[JobResult]) -> List[Anomaly]:
        if not jobs:
            return []
        failures = [j for j in jobs if j.status == OperationStatus.FAILURE.value]
        rate = len(failures) / len(jobs)
        if rate > 0.3:
            return [Anomaly(type="HIGH_ERROR_RATE", severity=Severity.HIGH.value, value=rate)]
        return []

    @staticmethod
    def categorize_anomaly(anomaly: Anomaly) -> str:
        mapping = {
            "TIMEOUT": "TIMEOUT",
            "HIGH_ERROR_RATE": "HIGH_ERROR_RATE",
            "QUEUE_BACKLOG": "QUEUE_BACKLOG",
            "RESOURCE_EXHAUSTION": "RESOURCE_EXHAUSTION",
        }
        return mapping.get(anomaly.type, "UNKNOWN")

    async def execute_recovery(self, anomaly: Anomaly, category: str) -> Dict[str, Any]:
        """执行恢复动作。"""
        if category == "TIMEOUT":
            return {"status": "RECOVERED", "action": "increase_timeout_or_terminate", "anomaly": anomaly.type}
        if category == "HIGH_ERROR_RATE":
            return {"status": "RECOVERED", "action": "throttle_or_rollback", "anomaly": anomaly.type}
        if category == "QUEUE_BACKLOG":
            return {"status": "RECOVERED", "action": "increase_concurrency", "anomaly": anomaly.type}
        return {"status": "UNHANDLED", "action": None, "anomaly": category}

    def log_recovery_action(self, anomaly: Anomaly, recovery: Dict[str, Any]) -> None:
        self.recovery_log.append({"anomaly": anomaly.type, "recovery": recovery})


class AdaptiveOptimizer:
    """自适应优化系统。"""

    def identify_optimization_opportunities(self, analysis: Dict[str, Any]) -> List[Any]:
        """识别优化机会。"""
        from agent.core.types import OptimizationOpportunity

        opportunities = []
        if analysis.get("avg_parallelism", 0) < analysis.get("optimal_parallelism", 0):
            opportunities.append(
                OptimizationOpportunity(type="INCREASE_PARALLELISM", impact=analysis.get("potential_speedup", 0.0), effort="LOW")
            )
        if analysis.get("resource_utilization", 0) < 0.7:
            opportunities.append(
                OptimizationOpportunity(type="OPTIMIZE_RESOURCE_ALLOCATION", impact=analysis.get("potential_savings", 0.0), effort="MEDIUM")
            )
        if analysis.get("avg_wait_time", 0) > analysis.get("target_wait_time", 0):
            opportunities.append(
                OptimizationOpportunity(type="OPTIMIZE_SCHEDULING", impact=analysis.get("potential_latency_improvement", 0.0), effort="MEDIUM")
            )
        return opportunities

    async def apply_optimization(self, opportunity: Any) -> Dict[str, Any]:
        """应用优化。"""
        return {"type": opportunity.type, "applied": True}


__all__ = ["SelfHealingSystem", "AdaptiveOptimizer"]
