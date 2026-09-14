"""
记忆系统 - 记忆层次迁移 (Memory Migration)

在记忆层之间迁移数据：
  Layer 1 → 2 (2h)  /  Layer 2 → 3 (30d)  /  Layer 3 → 4 (抽象)  /  Layer 4 → 5 (7y)

设计文档: 03_记忆系统架构.md
"""

from __future__ import annotations

import logging
from typing import Any, List

from agent.core.types import KnowledgeItem, SessionRecord, SystemEvent
from agent.memory.core.layers import (ArchiveMemory, EpisodicMemory,
                                      ImmediateContextMemory, SemanticMemory,
                                      SessionMemory)

logger = logging.getLogger(__name__)


class MemoryMigrationManager:
    """记忆层次迁移管理。"""

    def __init__(
        self,
        immediate: ImmediateContextMemory,
        session: SessionMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        archive: ArchiveMemory,
    ):
        self.immediate = immediate
        self.session = session
        self.episodic = episodic
        self.semantic = semantic
        self.archive = archive

    def migrate_between_layers(self) -> Dict[str, int]:
        """执行所有层间迁移，返回各迁移的数量。"""
        return {
            "layer_1_to_2": self.migrate_layer_1_to_2(),
            "layer_2_to_3": self.migrate_layer_2_to_3(),
            "layer_3_to_4": self.migrate_layer_3_to_4(),
            "layer_4_to_5": self.migrate_layer_4_to_5(),
        }

    def migrate_layer_1_to_2(self) -> int:
        """即时上下文 → 短期会话（会话历史迁移为会话记录）。"""
        count = 0
        turns = list(self.immediate.conversation_buffer)
        if not turns:
            return 0
        # 聚合为一个会话记录
        from agent.core.types import SessionContext

        context = SessionContext(
            session_id="migrated_session",
            conversation_history=turns,
        )
        self.session.store_session_context("migrated_session", context)
        self.immediate.conversation_buffer.clear()
        count = len(turns)
        logger.info("Migrated %d turns from L1 to L2", count)
        return count

    def migrate_layer_2_to_3(self) -> int:
        """短期会话 → 中期事件（会话摘要转事件）。"""
        count = 0
        for key in list(self.session.storage):
            record = self.session.retrieve(key)
            if isinstance(record, SessionRecord):
                event = SystemEvent(
                    type="session_completed",
                    actor=record.user_id,
                    action="session_summary",
                    resource=record.session_id,
                    result=record.summary,
                    success=True,
                )
                self.episodic.record_event(event)
                count += 1
        return count

    def migrate_layer_3_to_4(self) -> int:
        """事件记忆 → 语义记忆（提取模式合成知识项）。"""
        patterns = self.episodic.extract_learned_patterns()
        count = 0
        for pattern in patterns:
            item = KnowledgeItem(
                title=pattern.pattern_type,
                content=pattern.description,
                category="learned_pattern",
                context=f"confidence={pattern.confidence}",
            )
            self.semantic.store_knowledge_item(item)
            count += 1
        return count

    def migrate_layer_4_to_5(self) -> int:
        """语义记忆 → 永久存档（示例：知识项不自动归档，返回 0）。"""
        return 0


__all__ = ["MemoryMigrationManager"]
