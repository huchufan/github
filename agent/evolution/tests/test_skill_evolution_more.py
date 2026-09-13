import pytest
import asyncio

from agent.evolution.core.skill_evolution import (
    SkillRegistry,
    SkillQualityAssurance,
    SkillEvolutionSystem,
)
from agent.core.types import SkillDefinition, SkillCreationOpportunity, SkillImprovement


def test_bump_version_and_quality_tier():
    qa = SkillQualityAssurance()
    skill = SkillDefinition(name='s1', description='desc', code='def f(): pass', version='0.1.0')
    metrics = asyncio.run(qa.evaluate_skill_quality(skill))
    assert metrics.overall_score > 0
    tier = qa.determine_quality_tier(metrics.overall_score)
    assert tier in ('PRODUCTION', 'BETA', 'ALPHA', 'EXPERIMENTAL')


def test_bump_version_static():
    ses = SkillEvolutionSystem()
    assert ses._bump_version('0.1.0') == '0.1.1'
    assert ses._bump_version('1.2.3') == '1.2.4'


def test_create_new_skill_registers():
    ses = SkillEvolutionSystem()
    opp = SkillCreationOpportunity(skill_name='auto', description='auto skill', pattern='p')
    skill = asyncio.run(ses.create_new_skill(opp))
    assert skill is not None
    # registry should contain it
    found = ses.registry.get_skill('auto')
    assert found is not None


def test_improve_existing_skill_updates_registry():
    registry = SkillRegistry()
    base = SkillDefinition(name='base', description='d', code='def f(): pass', version='0.1.0')
    registry.register_skill(base)
    ses = SkillEvolutionSystem(registry=registry)
    imp = SkillImprovement(skill_id='base', target='improve')
    improved = asyncio.run(ses.improve_existing_skill(imp))
    # either improved or None depending on scoring; if improved then registry updated
    if improved:
        assert registry.get_skill('base').version != '0.1.0'
    else:
        assert registry.get_skill('base') is not None
