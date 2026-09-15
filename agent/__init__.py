"""
Hermes Agent - 自进化 AI 智能体系统

六大框架的完整落地实现：
  - governance   治理框架（规则与约束层）
  - orchestration 智能编排框架（执行编排层）
  - memory       记忆系统架构（认知基础层）
  - automation   自动化执行框架（运行时执行层）
  - evolution    自进化框架（学习进化层）
  - multiagent   多智能体管理架构（分布式协作层）

设计文档: 00_系统架构总览.md ~ 06_多智能体管理架构.md
默认模型: crazyroute/gpt-5-mini
版本: 1.0
"""

from agent.core import DEFAULT_MODEL

__version__ = "1.0.0"
__all__ = ["DEFAULT_MODEL", "__version__"]
