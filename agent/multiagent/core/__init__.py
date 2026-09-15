"""
多智能体管理架构 (Multi-Agent Framework)

Hermes 系统的分布式协作层：生命周期、角色、通信、任务分配、协作、集群管理、监控优化。

设计文档: 06_多智能体管理架构.md
"""

from agent.multiagent.core.cluster import AgentRegistry, ClusterScaler
from agent.multiagent.core.communication import AgentCommunicationBus
from agent.multiagent.core.coordination import (ResultAggregator,
                                                TaskDecompositionCoordinator)
from agent.multiagent.core.distribution import (LoadBalancer,
                                                TaskDistributionManager)
from agent.multiagent.core.lifecycle import (AgentHealthMonitor,
                                             AgentLifecycleManager)
from agent.multiagent.core.monitor import ClusterMonitor, ClusterOptimizer
from agent.multiagent.core.roles import ROLE_DEFINITIONS, AgentRoleManager

__all__ = [
    "AgentLifecycleManager",
    "AgentHealthMonitor",
    "AgentRoleManager",
    "ROLE_DEFINITIONS",
    "AgentCommunicationBus",
    "TaskDistributionManager",
    "LoadBalancer",
    "TaskDecompositionCoordinator",
    "ResultAggregator",
    "AgentRegistry",
    "ClusterScaler",
    "ClusterMonitor",
    "ClusterOptimizer",
]
