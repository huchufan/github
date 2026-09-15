"""
多智能体管理架构 (Multi-Agent Framework)
"""

from agent.multiagent.core import *  # noqa: F401,F403
from agent.multiagent.loader import load_registry

__all__: list = []

# Load registry at import time so other modules can access agent profiles
AGENT_REGISTRY = load_registry()

from agent.multiagent.startup import bootstrap_agents

# Run lightweight bootstrap validation on import
_bootstrap_summary = bootstrap_agents(AGENT_REGISTRY)

# Re-export convenience API
from agent.multiagent.api import get_agent

__all__ = ["AGENT_REGISTRY", "get_agent"]
