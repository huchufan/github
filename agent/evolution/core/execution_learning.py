"""
自进化框架 - 执行级学习 (Execution-Level Learning)

任务执行分析、成功/失败学习与决策参数优化。

设计文档: 05_自进化框架.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (
    ExecutionInsight,
    ExecutionResult,
    ExecutionTrace,
    FailureAnalysis,
    ImpactAnalysis,
    ParameterConstraints,
    RecoveryPattern,
    SuccessFactors,
    SuccessfulConfiguration,
)

logger = logging.getLogger(__name__)


class ExecutionLevelLearning:
    """执行级学习系统。"""

    def __init__(self):
        self.confidence_model: Dict[str, float] = {}
        self.successful_configs: List[SuccessfulConfiguration] = []
        self.recovery_patterns: List[RecoveryPattern] = []
        self.recovery_rules: Dict[str, RecoveryPattern] = {}

    async def analyze_execution(self, execution_result: ExecutionResult, execution_trace: ExecutionTrace) -> ExecutionInsight:
        """分析执行结果并提取洞察。"""
        insight = ExecutionInsight(execution_id=execution_result.execution_id)

        if execution_result.status == "SUCCESS":
            factors = self.extract_success_factors(execution_trace, execution_result)
            insight.success_patterns = factors
            await self.learn_from_success(factors)

        elif execution_result.status == "FAILURE":
            causes = self.analyze_failure_causes(execution_result.error or "", execution_trace)
            insight.failure_analysis = causes
            await self.learn_failure_recovery(causes)

        insight.performance_metrics = self.extract_performance_metrics(execution_trace)
        insight.resource_efficiency = self.calculate_resource_efficiency(execution_trace, execution_result)
        insight.decision_path = execution_trace.decisions

        return insight

    def extract_success_factors(self, trace: ExecutionTrace, result: ExecutionResult) -> SuccessFactors:
        skills = [s.get("skill", "") for s in trace.steps]
        return SuccessFactors(
            skills_used=skills,
            parameters={},
            execution_order=[s.get("task_id", "") for s in trace.steps],
            resource_usage=trace.resource_usage,
        )

    def analyze_failure_causes(self, error: str, trace: ExecutionTrace) -> FailureAnalysis:
        return FailureAnalysis(
            error_type="GENERIC_ERROR",
            root_cause=error,
            recovery_actions=["retry", "fallback"],
            recovery_success_rate=0.5,
        )

    @staticmethod
    def extract_performance_metrics(trace: ExecutionTrace) -> Dict[str, Any]:
        return {"steps": len(trace.steps), "resource_usage": trace.resource_usage}

    @staticmethod
    def calculate_resource_efficiency(trace: ExecutionTrace, result: ExecutionResult) -> float:
        return 1.0 if result.status == "SUCCESS" else 0.5

    async def learn_from_success(self, success_factors: SuccessFactors) -> None:
        """从成功中学习。"""
        config = SuccessfulConfiguration(
            skill_selection=success_factors.skills_used,
            parameter_values=success_factors.parameters,
            execution_order=success_factors.execution_order,
            resource_allocation=success_factors.resource_usage,
        )
        self.successful_configs.append(config)
        for skill in config.skill_selection:
            self.confidence_model[skill] = min(1.0, self.confidence_model.get(skill, 0.5) + 0.1)

    async def learn_failure_recovery(self, failure_causes: FailureAnalysis) -> None:
        """从失败中学习恢复策略。"""
        pattern = RecoveryPattern(
            failure_type=failure_causes.error_type,
            root_cause=failure_causes.root_cause,
            recovery_actions=failure_causes.recovery_actions,
            effectiveness=failure_causes.recovery_success_rate,
        )
        self.recovery_patterns.append(pattern)
        self.recovery_rules[pattern.failure_type] = pattern


class DecisionOptimizer:
    """决策优化引擎。"""

    async def optimize_decision_parameters(self, execution_insights: List[ExecutionInsight]) -> Dict[str, float]:
        """基于执行洞察优化决策参数。"""
        decision_history = self.collect_decision_history(execution_insights)
        impact = self.analyze_parameter_impact(decision_history)

        optimized: Dict[str, float] = {}
        for param_name, analysis in impact.items():
            optimal = await self.optimize_parameter_value(param_name, analysis, ParameterConstraints(0.0, 1.0))
            optimized[param_name] = optimal
        return optimized

    @staticmethod
    def collect_decision_history(insights: List[ExecutionInsight]) -> List[Dict[str, Any]]:
        return [{"decision_path": i.decision_path, "metrics": i.performance_metrics} for i in insights]

    def analyze_parameter_impact(self, history: List[Dict[str, Any]]) -> Dict[str, ImpactAnalysis]:
        """分析参数影响（简化：基于性能指标推断）。"""
        impact: Dict[str, ImpactAnalysis] = {}
        for entry in history:
            for step in entry.get("decision_path", []):
                if isinstance(step, dict):
                    for key in step.keys():
                        impact.setdefault(key, ImpactAnalysis(param_name=key))
        if not impact:
            impact["parallelism"] = ImpactAnalysis(param_name="parallelism", optimal_value=0.5)
        return impact

    async def optimize_parameter_value(self, param_name: str, analysis: ImpactAnalysis, constraints: ParameterConstraints) -> float:
        """优化单个参数（简化为区间中点，避免外部依赖）。"""
        return (constraints.min_value + constraints.max_value) / 2


__all__ = ["ExecutionLevelLearning", "DecisionOptimizer"]
