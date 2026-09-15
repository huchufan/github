import asyncio

import pytest

from agent.core.types import (SkillCreationOpportunity, SkillDefinition,
                              SkillImprovement)
from agent.evolution.core.skill_evolution import (SkillEvolutionSystem,
                                                  SkillQualityAssurance,
                                                  SkillRegistry)


def test_skill_quality_evaluation():
    qa = SkillQualityAssurance()
    skill = SkillDefinition(
        name="test", description="a test skill", code="def run(): pass", version="0.1.0"
    )
    metrics = asyncio.run(qa.evaluate_skill_quality(skill))
    assert metrics.overall_score >= 0.0
    assert metrics.quality_tier in ("PRODUCTION", "BETA", "ALPHA", "EXPERIMENTAL")


def test_create_new_skill():
    system = SkillEvolutionSystem()
    opp = SkillCreationOpportunity(
        skill_name="new_skill", description="auto", pattern="p1"
    )
    skill = asyncio.run(system.create_new_skill(opp))
    assert skill is not None
    assert system.registry.get_skill("new_skill") is not None
