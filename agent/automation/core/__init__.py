"""
自动化执行框架 (Automation Execution Framework)

Hermes 系统的运行时执行层：触发管理、调度引擎、工作流执行、负载均衡、自我修复。

设计文档: 04_自动化执行框架.md
"""

from agent.automation.core.executor import WorkflowExecutionEngine
from agent.automation.core.healing import AdaptiveOptimizer, SelfHealingSystem
from agent.automation.core.loadbalance import LoadBalancingManager
from agent.automation.core.scheduler import (PriorityQueue,
                                             ResourceAwareScheduler,
                                             SchedulingEngine)
from agent.automation.core.triggers import TriggerExecutor, TriggerManager

__all__ = [
    "TriggerManager",
    "TriggerExecutor",
    "PriorityQueue",
    "SchedulingEngine",
    "ResourceAwareScheduler",
    "WorkflowExecutionEngine",
    "LoadBalancingManager",
    "SelfHealingSystem",
    "AdaptiveOptimizer",
]
