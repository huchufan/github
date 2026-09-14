"""
自进化框架 - 系统级学习 (System-Level Learning)

架构演进分析与多智能体集群学习。

设计文档: 05_自进化框架.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (ArchitecturalImprovement, BottleneckAnalysis,
                              KnowledgeItem)

logger = logging.getLogger(__name__)


class ArchitecturalEvolution:
    """系统架构演进。"""

    def __init__(self):
        self.planned_changes: List[ArchitecturalImprovement] = []

    def identify_system_bottlenecks(
        self, metrics: Dict[str, float]
    ) -> BottleneckAnalysis:
        """识别系统瓶颈。"""
        analysis = BottleneckAnalysis()
        if metrics.get("pool_utilization", 0) > 0.9:
            analysis.add_bottleneck(
                "CONCURRENCY_LIMIT",
                "HIGH",
                "Increase worker pool or add multi-processing",
            )
        if metrics.get("storage_latency_ms", 0) > 100:
            analysis.add_bottleneck(
                "STORAGE_LATENCY", "MEDIUM", "Optimize indices or add caching layer"
            )
        if metrics.get("network_utilization", 0) > 0.8:
            analysis.add_bottleneck(
                "NETWORK_BANDWIDTH", "HIGH", "Add compression or reduce message size"
            )
        return analysis

    def generate_architectural_improvements(
        self, bottleneck: BottleneckAnalysis
    ) -> List[ArchitecturalImprovement]:
        """生成架构改进建议。"""
        return [
            ArchitecturalImprovement(
                type=b["type"],
                description=b["potential_improvement"],
                value_score=0.9,
                feasibility_score=0.8,
            )
            for b in bottleneck.bottlenecks
        ]

    async def evolve_system_architecture(
        self, metrics: Dict[str, float]
    ) -> List[ArchitecturalImprovement]:
        """演进系统架构，返回已计划的改进。"""
        bottlenecks = self.identify_system_bottlenecks(metrics)
        improvements = self.generate_architectural_improvements(bottlenecks)
        planned = []
        for imp in improvements:
            if imp.value_score > 0.8 and imp.feasibility_score > 0.7:
                self.planned_changes.append(imp)
                planned.append(imp)
        return planned


class ClusterLearningSystem:
    """多智能体集群学习。"""

    def __init__(self, agent_id: str = "agent-0"):
        self.agent_id = agent_id
        self.local_knowledge: List[KnowledgeItem] = []
        self.remote_knowledge: List[KnowledgeItem] = []

    def extract_valuable_knowledge(self) -> List[KnowledgeItem]:
        """提取本地有价值的知识。"""
        return [k for k in self.local_knowledge if k.content]

    async def integrate_remote_knowledge(self, knowledge_item: KnowledgeItem) -> bool:
        """集成远程知识。"""
        relevance = self.calculate_knowledge_relevance(knowledge_item)
        if relevance > 0.7:
            self.remote_knowledge.append(knowledge_item)
            return True
        return False

    async def share_knowledge_across_cluster(
        self, remote_pull: List[KnowledgeItem]
    ) -> List[KnowledgeItem]:
        """在集群中共享知识（模拟发布/拉取）。"""
        integrated = []
        for item in remote_pull:
            if await self.integrate_remote_knowledge(item):
                integrated.append(item)
        return integrated

    @staticmethod
    def calculate_knowledge_relevance(item: KnowledgeItem) -> float:
        # 简化：有内容且非空即视为高相关
        return 0.9 if item.content else 0.0


__all__ = ["ArchitecturalEvolution", "ClusterLearningSystem"]
