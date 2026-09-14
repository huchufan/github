"""
自进化框架 - 反馈循环和知识合成 (Feedback Loop & Knowledge Distillation)

用户反馈集成与知识蒸馏。

设计文档: 05_自进化框架.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import CorrectionFeedback, KnowledgeItem, UserFeedback

logger = logging.getLogger(__name__)


class UserFeedbackIntegration:
    """用户反馈集成。"""

    def __init__(self):
        self.prevention_rules: List[Dict[str, Any]] = []

    async def integrate_user_feedback(self, feedback: UserFeedback) -> Dict[str, Any]:
        """集成用户反馈。"""
        if feedback.type == "CORRECTION":
            return await self.learn_from_correction(
                CorrectionFeedback(content=feedback.content)
            )
        if feedback.type == "PREFERENCE":
            return {"type": "preference", "learned": True}
        if feedback.type == "FEATURE_REQUEST":
            return {"type": "feature_request", "recorded": True}
        if feedback.type == "BUG_REPORT":
            return {"type": "bug_report", "recorded": True}
        return {"type": "unknown", "recorded": False}

    def identify_error_root_cause(
        self, correction: CorrectionFeedback
    ) -> Dict[str, str]:
        """识别错误的根本原因。"""
        if "skill" in correction.content.lower():
            return {"type": "SKILL_ERROR"}
        if "decision" in correction.content.lower():
            return {"type": "DECISION_ERROR"}
        if "data" in correction.content.lower():
            return {"type": "DATA_ERROR"}
        return {"type": "GENERIC_ERROR"}

    async def learn_from_correction(
        self, correction: CorrectionFeedback
    ) -> Dict[str, Any]:
        """从用户纠正中学习。"""
        root_cause = self.identify_error_root_cause(correction)
        prevention = self.generate_prevention_rule(root_cause)
        self.prevention_rules.append(prevention)
        return {"root_cause": root_cause, "prevention_rule": prevention}

    @staticmethod
    def generate_prevention_rule(root_cause: Dict[str, str]) -> Dict[str, Any]:
        """生成预防规则。"""
        return {
            "type": root_cause["type"],
            "rule": f"avoid_{root_cause['type'].lower()}",
        }


class KnowledgeDistillation:
    """知识蒸馏和模型压缩。"""

    async def distill_knowledge(
        self, knowledge_items: List[KnowledgeItem]
    ) -> List[Dict[str, Any]]:
        """蒸馏知识为紧凑表示。"""
        clusters = self.cluster_knowledge(knowledge_items)
        results = []
        for cluster in clusters:
            compact = self.generate_compact_representation(cluster)
            validation = self.validate_compact_model(cluster, compact)
            if validation["compression_ratio"] > 1.0 and validation["accuracy"] > 0.9:
                results.append(compact)
        return results

    @staticmethod
    def cluster_knowledge(items: List[KnowledgeItem]) -> List[List[KnowledgeItem]]:
        """按类别聚类。"""
        clusters: Dict[str, List[KnowledgeItem]] = {}
        for item in items:
            clusters.setdefault(item.category or "general", []).append(item)
        return list(clusters.values())

    @staticmethod
    def generate_compact_representation(cluster: List[KnowledgeItem]) -> Dict[str, Any]:
        """为集群生成紧凑表示。"""
        if not cluster:
            return {}
        titles = [k.title for k in cluster]
        return {
            "category": cluster[0].category,
            "title": (
                titles[0]
                if len(titles) == 1
                else f"{titles[0]} (+{len(titles) - 1} more)"
            ),
            "item_count": len(cluster),
        }

    @staticmethod
    def validate_compact_model(
        original: List[KnowledgeItem], compact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证紧凑表示（压缩比 = 被压缩的知识项数量）。"""
        ratio = max(1.0, float(len(original)))
        return {"compression_ratio": ratio, "accuracy": 1.0}


__all__ = ["UserFeedbackIntegration", "KnowledgeDistillation"]
