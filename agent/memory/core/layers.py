"""
记忆系统 - 五层记忆存储 (Five-Layer Memory Storage)

Layer 1: 即时上下文记忆 (0-2h)
Layer 2: 短期会话记忆 (1-30d)
Layer 3: 中期事件记忆 (30-90d)
Layer 4: 长期语义记忆 (无限)
Layer 5: 永久存档记忆 (7y)

设计文档: 03_记忆系统架构.md
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from collections import OrderedDict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agent.core.types import (
    ArchiveReference,
    AttentionContext,
    ConversationContext,
    ConversationTurn,
    EventRecord,
    KnowledgeItem,
    KnowledgeRecord,
    SearchQuery,
    SearchResult,
    SessionContext,
    SessionRecord,
    SystemEvent,
    UserProfile,
    now,
)
from agent.core.errors import ArchiveCorruptedError, MemoryNotFoundError
from agent.memory.core.embeddings import EmbeddingModel, SemanticIndex

logger = logging.getLogger(__name__)


class LRUCache:
    """简单 LRU 缓存。"""

    def __init__(self, size: int = 100):
        self.size = size
        self._cache: "OrderedDict[Any, Any]" = OrderedDict()

    def get(self, key: Any) -> Optional[Any]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: Any, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.size:
            self._cache.popitem(last=False)

    def __contains__(self, key: Any) -> bool:
        return key in self._cache


# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------

class MemoryLayer(ABC):
    """记忆层基类。"""

    def __init__(self, name: str, ttl: Optional[timedelta] = None):
        self.name = name
        self.ttl = ttl
        self.storage: Dict[str, Any] = {}
        self.created_at: Dict[str, datetime] = {}

    @abstractmethod
    def store(self, key: str, value: Any) -> None:
        ...

    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Any]:
        ...

    def _is_expired(self, key: str) -> bool:
        if self.ttl is None:
            return False
        created = self.created_at.get(key)
        if created is None:
            return False
        return datetime.now() - created > self.ttl

    def cleanup_expired(self) -> int:
        """清理过期项，返回清理数量。"""
        expired = [k for k in list(self.storage) if self._is_expired(k)]
        for key in expired:
            del self.storage[key]
            self.created_at.pop(key, None)
        return len(expired)


# ---------------------------------------------------------------------------
# Layer 1: 即时上下文记忆
# ---------------------------------------------------------------------------

class ImmediateContextMemory(MemoryLayer):
    """第 1 层：即时上下文 (0-2h)。"""

    def __init__(self, max_size: int = 1000, ttl: timedelta = timedelta(hours=2)):
        super().__init__("immediate", ttl=ttl)
        self.max_size = max_size
        self.conversation_buffer: deque = deque(maxlen=max_size)
        self.execution_state: Dict[str, Any] = {}
        self.working_memory = LRUCache(size=100)
        self.attention_stack: List[Any] = []

    def store(self, key: str, value: Any) -> None:
        self.storage[key] = value
        self.created_at[key] = datetime.now()

    def retrieve(self, key: str) -> Optional[Any]:
        if key not in self.storage:
            return None
        if self._is_expired(key):
            del self.storage[key]
            self.created_at.pop(key, None)
            return None
        return self.storage[key]

    def search(self, query: str, limit: int = 10) -> List[Any]:
        results = []
        q = query.lower()
        for value in self.storage.values():
            if q in str(value).lower():
                results.append(value)
                if len(results) >= limit:
                    break
        return results

    def record_conversation_turn(self, user_message: str, agent_response: str, metadata: Optional[Dict] = None) -> ConversationTurn:
        """记录对话轮次。"""
        turn = ConversationTurn(
            user_message=user_message,
            agent_response=agent_response,
            metadata=metadata or {},
        )
        self.conversation_buffer.append(turn)
        return turn

    def get_conversation_context(self, window_size: int = 10) -> ConversationContext:
        """获取对话上下文。"""
        recent = list(self.conversation_buffer)[-window_size:]
        return ConversationContext(
            turns=recent,
            main_topic=self._extract_main_topic(recent),
            participant_intents=[t.user_intent for t in recent if t.user_intent],
            conversation_state="active" if recent else "idle",
            last_turn_time=recent[-1].timestamp if recent else None,
        )

    @staticmethod
    def _extract_main_topic(turns: List[ConversationTurn]) -> str:
        if not turns:
            return ""
        # 简单启发式：最近一轮用户消息的前几个词
        return turns[-1].user_message[:20]

    def update_execution_state(self, state_update: Dict[str, Any]) -> None:
        self.execution_state.update(state_update)
        self.execution_state["_updated_at"] = datetime.now()

    def get_attention_context(self) -> AttentionContext:
        if not self.attention_stack:
            return AttentionContext(items=[], primary=None)
        primary = self.attention_stack[0]
        secondary = self.attention_stack[1:] if len(self.attention_stack) > 1 else []
        return AttentionContext(
            items=self.attention_stack,
            primary=primary,
            secondary=secondary,
            focus_strength=1.0 / len(self.attention_stack) if self.attention_stack else 0.0,
        )


# ---------------------------------------------------------------------------
# Layer 2: 短期会话记忆
# ---------------------------------------------------------------------------

class SessionMemory(MemoryLayer):
    """第 2 层：短期会话 (1-30d)。"""

    def __init__(self, ttl: timedelta = timedelta(days=30)):
        super().__init__("session", ttl=ttl)
        self.cache = LRUCache(size=10000)

    def store(self, key: str, value: Any) -> None:
        self.storage[key] = value
        self.created_at[key] = datetime.now()
        self.cache.put(key, value)

    def retrieve(self, key: str) -> Optional[Any]:
        if key in self.cache:
            return self.cache.get(key)
        if key not in self.storage:
            return None
        if self._is_expired(key):
            del self.storage[key]
            return None
        value = self.storage[key]
        self.cache.put(key, value)
        return value

    def search(self, query: str, limit: int = 10) -> List[Any]:
        q = query.lower()
        results = []
        for key, value in self.storage.items():
            record = value
            text = self._record_text(record).lower()
            if q in text:
                results.append(record)
                if len(results) >= limit:
                    break
        return results

    @staticmethod
    def _record_text(record: Any) -> str:
        if isinstance(record, SessionRecord):
            return record.summary + " " + " ".join(record.key_decisions)
        return str(record)

    def store_session_context(self, session_id: str, context: SessionContext) -> SessionRecord:
        """存储会话上下文。"""
        record = SessionRecord(
            session_id=session_id,
            conversation_history=context.conversation_history,
            user_preferences={
                "communication_style": context.user_style,
                "technical_level": context.technical_level,
                "language": context.language,
                "response_format": context.response_format,
            },
            session_variables=context.variables,
            session_goals=context.goals,
            message_count=len(context.conversation_history),
            summary=self._summarize(context),
            key_decisions=[],
        )
        self.store(session_id, record)
        return record

    @staticmethod
    def _summarize(context: SessionContext) -> str:
        if not context.conversation_history:
            return ""
        return " | ".join(t.user_message[:40] for t in context.conversation_history[-3:])

    def retrieve_session_context(self, session_id: str) -> Optional[SessionRecord]:
        value = self.retrieve(session_id)
        return value if isinstance(value, SessionRecord) else None

    def search_sessions(self, query: SearchQuery) -> List[SessionRecord]:
        results = self.search(query.topic, limit=query.limit)
        return [r for r in results if isinstance(r, SessionRecord)]


# ---------------------------------------------------------------------------
# Layer 3: 中期事件记忆
# ---------------------------------------------------------------------------

class EpisodicMemory(MemoryLayer):
    """第 3 层：中期事件 (30-90d)。"""

    def __init__(self, ttl: timedelta = timedelta(days=90)):
        super().__init__("episodic", ttl=ttl)

    def store(self, key: str, value: Any) -> None:
        self.storage[key] = value
        self.created_at[key] = datetime.now()

    def retrieve(self, key: str) -> Optional[Any]:
        if key not in self.storage:
            return None
        if self._is_expired(key):
            del self.storage[key]
            return None
        return self.storage[key]

    def search(self, query: str, limit: int = 10) -> List[Any]:
        q = query.lower()
        results = []
        for value in self.storage.values():
            if q in str(value).lower():
                results.append(value)
                if len(results) >= limit:
                    break
        return results

    def record_event(self, event: SystemEvent) -> EventRecord:
        """记录系统事件。"""
        record = EventRecord(
            event_type=event.type,
            actor=event.actor,
            action=event.action,
            resource=event.resource,
            context={
                "session_id": event.session_id,
                "conversation_id": event.conversation_id,
                "related_events": event.related_event_ids,
            },
            result=event.result,
            success=event.success,
            error=event.error if not event.success else None,
            consequences=event.consequences,
            tags=self._generate_event_tags(event),
        )
        self.store(record.event_id, record)
        return record

    @staticmethod
    def _generate_event_tags(event: SystemEvent) -> List[str]:
        tags = [event.type, "success" if event.success else "failure"]
        if event.action:
            tags.append(event.action)
        return tags

    def get_events_in_window(self, time_window: timedelta = timedelta(days=30)) -> List[EventRecord]:
        cutoff = now() - time_window
        return [r for r in self.storage.values() if isinstance(r, EventRecord) and r.timestamp >= cutoff]

    def extract_learned_patterns(self, time_window: timedelta = timedelta(days=30)) -> List[Any]:
        """提取学习到的模式（简化实现）。"""
        from agent.core.types import LearnedPattern

        events = self.get_events_in_window(time_window)
        success = [e for e in events if e.success]
        failures = [e for e in events if not e.success]

        patterns: List[LearnedPattern] = []
        if success:
            common_action = max({e.action for e in success}, key=lambda a: sum(1 for e in success if e.action == a))
            patterns.append(LearnedPattern(pattern_type="success_sequence", description=f"Common successful action: {common_action}", confidence=0.7))
        if failures:
            common_error = max({e.error or "" for e in failures}, key=lambda a: sum(1 for e in failures if (e.error or "") == a))
            patterns.append(LearnedPattern(pattern_type="failure_recovery", description=f"Common error: {common_error}", confidence=0.6))
        return patterns

    def search_events(self, query: str, limit: int = 10) -> List[EventRecord]:
        return [r for r in self.search(query, limit) if isinstance(r, EventRecord)]


# ---------------------------------------------------------------------------
# Layer 4: 长期语义记忆
# ---------------------------------------------------------------------------

class SemanticMemory(MemoryLayer):
    """第 4 层：长期语义 (无时间限制)。"""

    def __init__(self, dim: int = 256):
        super().__init__("semantic", ttl=None)
        self.embedding_model = EmbeddingModel(dim=dim)
        self.semantic_index = SemanticIndex(dim=dim)

    def store(self, key: str, value: Any) -> None:
        self.storage[key] = value
        self.created_at[key] = datetime.now()

    def retrieve(self, key: str) -> Optional[Any]:
        return self.storage.get(key)

    def search(self, query: str, limit: int = 10) -> List[Any]:
        return self.semantic_search(query, top_k=limit)

    def store_knowledge_item(self, item: KnowledgeItem) -> KnowledgeRecord:
        """存储知识项。"""
        embedding = self.embedding_model.encode(f"{item.title} {item.content} {item.context}")
        record = KnowledgeRecord(
            title=item.title,
            content=item.content,
            category=item.category,
            concepts=item.concepts,
            relationships=item.relationships,
            source=item.source,
            embedding=embedding,
            keywords=self._extract_keywords(item),
            tags=item.tags,
            domain=item.domain,
        )
        self.store(record.knowledge_id, record)
        self.semantic_index.add(record.knowledge_id, embedding)
        return record

    @staticmethod
    def _extract_keywords(item: KnowledgeItem) -> List[str]:
        import re

        words = re.findall(r"[\w\u4e00-\u9fff]+", item.title + " " + item.content)
        return list(dict.fromkeys(words))[:10]

    def semantic_search(self, query: str, top_k: int = 10, threshold: float = 0.0) -> List[SearchResult]:
        """语义搜索。"""
        query_embedding = self.embedding_model.encode(query)
        vector_results = self.semantic_index.search(query_embedding, top_k=top_k * 2)

        results: List[SearchResult] = []
        for item_id, similarity in vector_results:
            if similarity < threshold:
                continue
            record = self.storage.get(item_id)
            if record is None:
                continue
            results.append(
                SearchResult(
                    knowledge_id=record.knowledge_id,
                    title=record.title,
                    summary=record.content[:120],
                    relevance_score=similarity,
                    source=record.source,
                    relationships=record.relationships,
                    layer=self.name,
                )
            )
            if len(results) >= top_k:
                break
        return results

    def build_knowledge_graph(self) -> Dict[str, Any]:
        """构建知识图谱（节点 + 边）。"""
        nodes = []
        edges = []
        for record in self.storage.values():
            if not isinstance(record, KnowledgeRecord):
                continue
            nodes.append({"id": record.knowledge_id, "label": record.title, "category": record.category})
            for rel in record.relationships:
                edges.append({"source": record.knowledge_id, "target": rel.get("target_id"), "type": rel.get("type"), "weight": rel.get("strength", 1.0)})
        return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Layer 5: 永久存档记忆
# ---------------------------------------------------------------------------

class ArchiveMemory(MemoryLayer):
    """第 5 层：永久存档 (7y)。"""

    def __init__(self, retention_period: timedelta = timedelta(days=2555)):
        super().__init__("archive", ttl=retention_period)
        self.archive_refs: Dict[str, ArchiveReference] = {}

    def store(self, key: str, value: Any) -> None:
        self.storage[key] = value
        self.created_at[key] = datetime.now()

    def retrieve(self, key: str) -> Optional[Any]:
        return self.storage.get(key)

    def search(self, query: str, limit: int = 10) -> List[Any]:
        q = query.lower()
        return [v for v in self.storage.values() if q in str(v).lower()][:limit]

    def archive_session(self, session: SessionRecord) -> ArchiveReference:
        """存档会话。"""
        compressed = self._compress(session)
        checksum = self._checksum(compressed)
        ref = ArchiveReference(
            session_id=session.session_id,
            archive_path=f"archive://{session.session_id}",
            user_id=session.user_id,
            date=session.created_at.date(),
            size=len(compressed),
            access_control=session.access_control,
            checksum=checksum,
        )
        self.store(ref.archive_id, ref)
        self.storage[ref.archive_id + ":data"] = compressed
        self.archive_refs[ref.archive_id] = ref
        return ref

    def retrieve_archived_session(self, archive_id: str) -> Optional[SessionRecord]:
        """检索存档会话。"""
        ref = self.archive_refs.get(archive_id)
        if ref is None:
            return None
        compressed = self.storage.get(archive_id + ":data")
        if compressed is None:
            raise ArchiveCorruptedError(archive_id)
        if self._checksum(compressed) != ref.checksum:
            raise ArchiveCorruptedError(archive_id)
        return self._decompress(compressed)

    @staticmethod
    def _compress(session: SessionRecord) -> bytes:
        return json.dumps(session.__dict__, default=str, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _decompress(data: bytes) -> SessionRecord:
        return SessionRecord(**json.loads(data.decode("utf-8")))

    @staticmethod
    def _checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


__all__ = [
    "MemoryLayer",
    "LRUCache",
    "ImmediateContextMemory",
    "SessionMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "ArchiveMemory",
]
