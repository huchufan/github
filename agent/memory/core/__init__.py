"""
记忆系统 (Memory System Architecture)

Hermes 系统的认知基础层：五层记忆存储、语义检索、用户建模、记忆迁移与融合。

设计文档: 03_记忆系统架构.md
"""

from agent.memory.core.embeddings import (
    embed,
    cosine_similarity,
    SemanticIndex,
    EmbeddingModel,
    DEFAULT_DIM,
)
from agent.memory.core.layers import (
    MemoryLayer,
    LRUCache,
    ImmediateContextMemory,
    SessionMemory,
    EpisodicMemory,
    SemanticMemory,
    ArchiveMemory,
)
from agent.memory.core.user_model import UserPreferenceModel, UserModel
from agent.memory.core.migration import MemoryMigrationManager
from agent.memory.core.retrieval import MemoryRetrievalEngine

__all__ = [
    # 嵌入
    "embed",
    "cosine_similarity",
    "SemanticIndex",
    "EmbeddingModel",
    "DEFAULT_DIM",
    # 分层存储
    "MemoryLayer",
    "LRUCache",
    "ImmediateContextMemory",
    "SessionMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "ArchiveMemory",
    # 用户建模
    "UserPreferenceModel",
    "UserModel",
    # 迁移与检索
    "MemoryMigrationManager",
    "MemoryRetrievalEngine",
]
from .search import Search
from .fusion import Fusion
