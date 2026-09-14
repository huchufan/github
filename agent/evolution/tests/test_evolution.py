"""自进化框架测试"""

import asyncio

from agent.core.types import (ExecutionResult, ExecutionTrace, KnowledgeItem,
                              SkillCreationOpportunity, SkillDefinition,
                              SkillImprovement, UserFeedback)
from agent.evolution.core.execution_learning import (DecisionOptimizer,
                                                     ExecutionLevelLearning)
from agent.evolution.core.feedback import (KnowledgeDistillation,
                                           UserFeedbackIntegration)
from agent.evolution.core.skill_evolution import (SkillEvolutionSystem,
                                                  SkillQualityAssurance,
                                                  SkillRegistry)
from agent.evolution.core.strategy import (OrchestrationStrategyOptimization,
                                           SchedulingStrategyOptimization)
from agent.evolution.core.system import (ArchitecturalEvolution,
                                         ClusterLearningSystem)


class TestExecutionLearning:
    def test_analyze_success(self):
        learner = ExecutionLevelLearning()
        result = ExecutionResult(status="SUCCESS", execution_id="e1")
        trace = ExecutionTrace(
            execution_id="e1", steps=[{"task_id": "t0", "skill": "s1"}]
        )
        insight = asyncio.run(learner.analyze_execution(result, trace))
        assert insight.success_patterns is not None
        assert "s1" in learner.confidence_model

    def test_analyze_failure(self):
        learner = ExecutionLevelLearning()
        result = ExecutionResult(status="FAILURE", execution_id="e2", error="boom")
        trace = ExecutionTrace(execution_id="e2")
        insight = asyncio.run(learner.analyze_execution(result, trace))
        assert insight.failure_analysis is not None

    def test_decision_optimizer(self):
        optimizer = DecisionOptimizer()
        insights = []
        result = asyncio.run(optimizer.optimize_decision_parameters(insights))
        assert "parallelism" in result


class TestSkillEvolution:
    def test_quality_evaluation(self):
        qa = SkillQualityAssurance()
        skill = SkillDefinition(
            name="test", description="a test skill", code="def run(): pass"
        )
        metrics = asyncio.run(qa.evaluate_skill_quality(skill))
        assert metrics.overall_score > 0.5
        assert metrics.quality_tier in ("PRODUCTION", "BETA", "ALPHA", "EXPERIMENTAL")

    def test_create_new_skill(self):
        system = SkillEvolutionSystem()
        opp = SkillCreationOpportunity(
            skill_name="new_skill", description="auto", pattern="p1"
        )
        skill = asyncio.run(system.create_new_skill(opp))
        assert skill is not None
        assert system.registry.get_skill("new_skill") is not None


class TestStrategyOptimization:
    def test_orchestration_strategy(self):
        optimizer = OrchestrationStrategyOptimization()
        data = [{"parallelism": 0.5}]
        applied = asyncio.run(optimizer.optimize_orchestration_strategies(data))
        assert isinstance(applied, list)
        assert optimizer.current_strategy is not None

    def test_scheduling_strategy(self):
        optimizer = SchedulingStrategyOptimization()
        weights = asyncio.run(optimizer.optimize_scheduling_strategy())
        assert "priority_weight" in weights


class TestSystemLearning:
    def test_architectural_evolution(self):
        evo = ArchitecturalEvolution()
        planned = asyncio.run(
            evo.evolve_system_architecture(
                {
                    "pool_utilization": 0.95,
                    "storage_latency_ms": 150,
                    "network_utilization": 0.5,
                }
            )
        )
        assert len(planned) >= 1

    def test_cluster_learning(self):
        system = ClusterLearningSystem()
        items = [KnowledgeItem(title="t1", content="useful knowledge", category="dev")]
        integrated = asyncio.run(system.share_knowledge_across_cluster(items))
        assert len(integrated) == 1


class TestFeedbackAndDistillation:
    def test_correction_feedback(self):
        integration = UserFeedbackIntegration()
        feedback = UserFeedback(type="CORRECTION", content="skill error occurred")
        result = asyncio.run(integration.integrate_user_feedback(feedback))
        assert result["root_cause"]["type"] == "SKILL_ERROR"
        assert len(integration.prevention_rules) == 1

    def test_knowledge_distillation(self):
        distillation = KnowledgeDistillation()
        items = [
            KnowledgeItem(title="a", content="x", category="dev"),
            KnowledgeItem(title="b", content="y", category="dev"),
            KnowledgeItem(title="c", content="z", category="food"),
            KnowledgeItem(title="d", content="w", category="food"),
        ]
        compact = asyncio.run(distillation.distill_knowledge(items))
        assert len(compact) == 2  # 两个类别，各有 2 项知识被蒸馏
