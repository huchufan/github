"""记忆系统测试"""

import asyncio

from agent.core.types import (ConversationTurn, KnowledgeItem, SessionContext,
                              SessionRecord, SystemEvent, UserHistory)
from agent.memory.core.embeddings import (EmbeddingModel, SemanticIndex,
                                          cosine_similarity, embed)
from agent.memory.core.layers import (ArchiveMemory, EpisodicMemory,
                                      ImmediateContextMemory, SemanticMemory,
                                      SessionMemory)
from agent.memory.core.migration import MemoryMigrationManager
from agent.memory.core.retrieval import MemoryRetrievalEngine
from agent.memory.core.user_model import UserModel, UserPreferenceModel


class TestEmbeddings:
    def test_embedding_shape_and_norm(self):
        vec = embed("hello world")
        assert len(vec) == 256
        norm = sum(v * v for v in vec)
        assert abs(norm - 1.0) < 1e-6

    def test_similarity(self):
        a = embed("python programming")
        b = embed("python programming")
        c = embed("cooking recipe")
        assert cosine_similarity(a, b) > 0.99
        assert cosine_similarity(a, c) < cosine_similarity(a, b)

    def test_semantic_index_search(self):
        idx = SemanticIndex()
        idx.add("1", embed("machine learning"))
        idx.add("2", embed("data science"))
        results = idx.search(embed("machine learning"), top_k=1)
        assert results[0][0] == "1"


class TestLayers:
    def test_immediate_context(self):
        mem = ImmediateContextMemory()
        mem.store("k", "value")
        assert mem.retrieve("k") == "value"
        turn = mem.record_conversation_turn("hi", "hello")
        ctx = mem.get_conversation_context()
        assert ctx.conversation_state == "active"
        assert ctx.turns[-1].user_message == "hi"

    def test_session_memory_store_retrieve(self):
        mem = SessionMemory()
        ctx = SessionContext(session_id="s1", user_style="concise")
        mem.store_session_context("s1", ctx)
        record = mem.retrieve_session_context("s1")
        assert record is not None
        assert record.user_preferences["communication_style"] == "concise"

    def test_episodic_memory(self):
        mem = EpisodicMemory()
        event = SystemEvent(type="task", actor="u1", action="execute", success=True)
        record = mem.record_event(event)
        assert record.success
        patterns = mem.extract_learned_patterns()
        assert len(patterns) >= 1

    def test_semantic_search(self):
        mem = SemanticMemory()
        mem.store_knowledge_item(
            KnowledgeItem(
                title="python", content="python programming language", category="dev"
            )
        )
        mem.store_knowledge_item(
            KnowledgeItem(title="cooking", content="how to cook pasta", category="food")
        )
        results = mem.semantic_search("python code", top_k=1)
        assert results[0].title == "python"
        graph = mem.build_knowledge_graph()
        assert len(graph["nodes"]) == 2

    def test_archive_roundtrip(self):
        archive = ArchiveMemory()
        session = SessionRecord(session_id="s1", user_id="u1", summary="test")
        ref = archive.archive_session(session)
        restored = archive.retrieve_archived_session(ref.archive_id)
        assert restored.session_id == "s1"
        assert restored.summary == "test"


class TestMigrationAndRetrieval:
    def _make_stack(self):
        immediate = ImmediateContextMemory()
        session = SessionMemory()
        episodic = EpisodicMemory()
        semantic = SemanticMemory()
        archive = ArchiveMemory()
        return immediate, session, episodic, semantic, archive

    def test_migration(self):
        immediate, session, episodic, semantic, archive = self._make_stack()
        immediate.record_conversation_turn("hi", "hello")
        manager = MemoryMigrationManager(
            immediate, session, episodic, semantic, archive
        )
        result = manager.migrate_between_layers()
        assert result["layer_1_to_2"] >= 1

    def test_retrieval_fusion(self):
        immediate, session, episodic, semantic, archive = self._make_stack()
        semantic.store_knowledge_item(
            KnowledgeItem(title="python", content="python code", category="dev")
        )
        engine = MemoryRetrievalEngine(immediate, session, episodic, semantic, archive)
        result = engine.retrieve_relevant_memory("python")
        assert result.fused is not None
        assert result.layer_4


class TestUserModel:
    def test_preferences(self):
        sessions = [
            SessionRecord(
                user_id="u1",
                user_preferences={
                    "communication_style": "concise",
                    "technical_level": "expert",
                },
            ),
            SessionRecord(
                user_id="u1",
                user_preferences={
                    "communication_style": "concise",
                    "technical_level": "expert",
                },
            ),
        ]
        model = UserPreferenceModel()
        profile = model.learn_user_preferences(sessions)
        assert profile.communication_style == "concise"
        assert profile.technical_level == "expert"

    def test_comprehensive_model(self):
        model = UserModel()
        history = UserHistory(
            user_id="u1", sessions=[SessionRecord(user_id="u1", summary="python ml")]
        )
        result = model.build_comprehensive_user_model(history)
        assert result.user_id == "u1"
        assert result.preference_profile is not None
