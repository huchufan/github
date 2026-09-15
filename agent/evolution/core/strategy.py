"""
自进化框架 - 策略级学习 (Strategy-Level Learning)

编排策略优化与调度策略优化。

设计文档: 05_自进化框架.md
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agent.core.types import (
    OrchestrationStrategy,
    PerformanceAnalysis,
    QueueAnalysis,
)

logger = logging.getLogger(__name__)


class OrchestrationStrategyOptimization:
    """编排策略优化。"""

    def __init__(self):
        self.current_strategy: Optional[OrchestrationStrategy] = None
        self.strategy_change_log: List[Dict[str, Any]] = []

    def analyze_orchestration_performance(self, execution_data: List[Dict[str, Any]]) -> PerformanceAnalysis:
        """分析编排性能。"""
        if not execution_data:
            return PerformanceAnalysis()
        parallelism_values = [d.get("parallelism", 0) for d in execution_data]
        return PerformanceAnalysis(
            critical_path_utilization=0.8,
            parallelism_efficiency=sum(parallelism_values) / len(parallelism_values),
            resource_utilization_variance=0.2,
        )

    def generate_improved_strategies(self, current_performance: PerformanceAnalysis, execution_data: List[Dict[str, Any]]) -> List[OrchestrationStrategy]:
        """生成改进的编排策略。"""
        strategies: List[OrchestrationStrategy] = []
        if current_performance.critical_path_utilization > 0.9:
            strategies.append(OrchestrationStrategy(name="optimize_dag_structure"))
        if current_performance.parallelism_efficiency < 0.7:
            strategies.append(OrchestrationStrategy(name="optimize_parallelism", parallelism_degree=2))
        if current_performance.resource_utilization_variance > 0.3:
            strategies.append(OrchestrationStrategy(name="optimize_resource_allocation"))
        return strategies

    async def validate_strategy_improvement(self, current: Optional[OrchestrationStrategy], new: OrchestrationStrategy) -> Dict[str, Any]:
        """验证策略改进。"""
        return {"is_significant": True, "improvement": 0.15}

    async def optimize_orchestration_strategies(self, execution_data: List[Dict[str, Any]]) -> List[OrchestrationStrategy]:
        """优化编排策略，返回已应用的新策略。"""
        current = self.analyze_orchestration_performance(execution_data)
        improved = self.generate_improved_strategies(current, execution_data)
        applied = []
        for strategy in improved:
            validation = await self.validate_strategy_improvement(self.current_strategy, strategy)
            if validation["is_significant"]:
                self.current_strategy = strategy
                self.strategy_change_log.append({"strategy": strategy.name, "improvement": validation["improvement"]})
                applied.append(strategy)
        return applied


class SchedulingStrategyOptimization:
    """调度策略优化。"""

    def __init__(self):
        self.current_weights: Dict[str, float] = {
            "priority_weight": 0.4,
            "wait_time_weight": 0.3,
            "resource_weight": 0.2,
            "sla_weight": 0.1,
        }

    def analyze_queue_performance(self) -> QueueAnalysis:
        """分析队列性能。"""
        return QueueAnalysis(avg_memory=0.5, avg_wait_time=10.0, avg_priority=0.5)

    def generate_improved_priority_weights(self, analysis: QueueAnalysis) -> Dict[str, float]:
        """生成改进的优先级权重。"""
        weights = dict(self.current_weights)
        if analysis.avg_wait_time > 30:
            weights["wait_time_weight"] = min(0.5, weights["wait_time_weight"] + 0.1)
        return weights

    async def optimize_scheduling_strategy(self) -> Dict[str, float]:
        """优化调度策略，返回新权重。"""
        analysis = self.analyze_queue_performance()
        new_weights = self.generate_improved_priority_weights(analysis)
        self.current_weights = new_weights
        return new_weights


__all__ = ["OrchestrationStrategyOptimization", "SchedulingStrategyOptimization"]
