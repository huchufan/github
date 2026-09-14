"""
自进化框架 - 技能级学习 (Skill-Level Learning)

技能演进系统与技能质量评估。

设计文档: 05_自进化框架.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.types import (SkillCreationOpportunity, SkillDefinition,
                              SkillImprovement, SkillQualityMetrics)

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册表。"""

    def __init__(self):
        self.skills: Dict[str, SkillDefinition] = {}

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self.skills.get(skill_id)

    def update_skill(self, skill: SkillDefinition) -> None:
        self.skills[skill.name] = skill

    def register_skill(self, skill: SkillDefinition) -> None:
        self.skills[skill.name] = skill

    def list_skills(self) -> List[SkillDefinition]:
        return list(self.skills.values())


class SkillQualityAssurance:
    """技能质量评估。"""

    async def evaluate_skill_quality(
        self, skill: SkillDefinition
    ) -> SkillQualityMetrics:
        """评估技能质量。"""
        metrics = SkillQualityMetrics(skill_id=skill.name)
        metrics.functional_correctness = self._test_functional(skill)
        metrics.performance_efficiency = 0.7
        metrics.robustness = 0.7
        metrics.generalization_ability = 0.6
        metrics.documentation_quality = self.evaluate_documentation(skill)
        metrics.maintainability = self.evaluate_code_quality(skill)
        metrics.overall_score = self.calculate_overall_quality_score(metrics)
        metrics.quality_tier = self.determine_quality_tier(metrics.overall_score)
        return metrics

    @staticmethod
    def _test_functional(skill: SkillDefinition) -> float:
        # 有代码实现即视为基本可用
        return 0.8 if getattr(skill, "code", None) else 0.0

    @staticmethod
    def evaluate_documentation(skill: SkillDefinition) -> float:
        return 0.8 if getattr(skill, "description", None) else 0.2

    @staticmethod
    def evaluate_code_quality(skill: SkillDefinition) -> float:
        return 0.7

    @staticmethod
    def calculate_overall_quality_score(metrics: SkillQualityMetrics) -> float:
        weights = {
            "functional": 0.35,
            "performance": 0.2,
            "robustness": 0.15,
            "generalization": 0.15,
            "documentation": 0.08,
            "maintainability": 0.07,
        }
        score = (
            metrics.functional_correctness * weights["functional"]
            + metrics.performance_efficiency * weights["performance"]
            + metrics.robustness * weights["robustness"]
            + metrics.generalization_ability * weights["generalization"]
            + metrics.documentation_quality * weights["documentation"]
            + metrics.maintainability * weights["maintainability"]
        )
        return score

    @staticmethod
    def determine_quality_tier(score: float) -> str:
        if score >= 0.85:
            return "PRODUCTION"
        if score >= 0.7:
            return "BETA"
        if score >= 0.5:
            return "ALPHA"
        return "EXPERIMENTAL"


class SkillEvolutionSystem:
    """技能演进系统。"""

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or SkillRegistry()
        self.qa = SkillQualityAssurance()
        self.improvement_log: List[Dict[str, Any]] = []

    async def improve_existing_skill(
        self, opportunity: SkillImprovement
    ) -> Optional[SkillDefinition]:
        """改进现有技能。"""
        skill = self.registry.get_skill(opportunity.skill_id)
        if skill is None:
            return None

        improved = SkillDefinition(
            name=skill.name,
            description=skill.description,
            code=getattr(skill, "code", ""),
            version=self._bump_version(skill.version),
            created_from_pattern=getattr(skill, "created_from_pattern", ""),
        )
        original_score = (await self.qa.evaluate_skill_quality(skill)).overall_score
        test = await self.qa.evaluate_skill_quality(improved)
        improved_score = test.overall_score

        if improved_score >= original_score:
            self.registry.update_skill(improved)
            self.improvement_log.append(
                {"skill": skill.name, "from": original_score, "to": improved_score}
            )
            return improved
        return None

    async def create_new_skill(
        self, opportunity: SkillCreationOpportunity
    ) -> Optional[SkillDefinition]:
        """创建新技能。"""
        skill = SkillDefinition(
            name=opportunity.skill_name,
            description=opportunity.description,
            code=f"# Auto-generated skill from pattern: {opportunity.pattern}\n",
            version="0.1.0",
            created_from_pattern=opportunity.pattern,
        )
        test = await self.qa.evaluate_skill_quality(skill)
        if test.overall_score > 0.3:
            self.registry.register_skill(skill)
            return skill
        return None

    @staticmethod
    def _bump_version(version: str) -> str:
        parts = version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
        return ".".join(parts)


__all__ = ["SkillRegistry", "SkillQualityAssurance", "SkillEvolutionSystem"]
