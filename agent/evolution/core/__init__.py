"""
自进化框架 (Self-Evolution Framework)

Hermes 系统的学习进化层：执行级学习、技能级学习、策略级学习、系统级学习、反馈循环。

设计文档: 05_自进化框架.md
"""

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

__all__ = [
    "ExecutionLevelLearning",
    "DecisionOptimizer",
    "SkillRegistry",
    "SkillQualityAssurance",
    "SkillEvolutionSystem",
    "OrchestrationStrategyOptimization",
    "SchedulingStrategyOptimization",
    "ArchitecturalEvolution",
    "ClusterLearningSystem",
    "UserFeedbackIntegration",
    "KnowledgeDistillation",
]
from .analyzer import Analyzer
from .distiller import Distiller
from .learner import Learner
from .optimizer import Optimizer
