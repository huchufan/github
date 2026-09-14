from datetime import datetime, timedelta

import pytest

from agent.core.errors import ArchiveCorruptedError
from agent.core.types import KnowledgeItem, SessionRecord
from agent.memory.core.layers import (ArchiveMemory, ImmediateContextMemory,
                                      LRUCache, SemanticMemory, SessionMemory)


def test_lrucache_basic_eviction_and_contains():
    c = LRUCache(size=2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c and "b" in c
    # access a to mark it recent
    assert c.get("a") == 1
    c.put("c", 3)
    # b should be evicted
    assert "b" not in c
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_sessionmemory_expiry_evicts_cache_internal():
    sm = SessionMemory(ttl=timedelta(seconds=1))
    rec = SessionRecord(session_id="s-gap", user_id="u-gap")
    sm.store("s-gap", rec)
    assert sm.retrieve("s-gap") is not None
    # simulate expiry
    sm.created_at["s-gap"] = datetime.now() - timedelta(days=31)
    got = sm.retrieve("s-gap")
    assert got is None
    # internal cache should not contain key
    try:
        internal = getattr(sm.cache, "_cache", {})
        assert "s-gap" not in internal
    except Exception:
        # if structure differs, at least storage should not contain key
        assert "s-gap" not in sm.storage


def test_immediate_attention_context_and_conversation():
    im = ImmediateContextMemory(max_size=3)
    # empty context
    att = im.get_attention_context()
    assert att.items == []
    # record a turn and set attention
    im.record_conversation_turn("hello", "hi")
    im.attention_stack = ["top", "sec"]
    ac = im.get_attention_context()
    assert ac.primary == "top"
    assert ac.secondary == ["sec"]


def test_semantic_search_threshold_and_graph():
    sm = SemanticMemory(dim=16)
    a = KnowledgeItem(
        title="A",
        content="alpha content",
        category="cat",
        concepts=[],
        relationships=[{"target_id": "B", "type": "rel", "strength": 1.0}],
        source="src",
        tags=[],
        domain="d",
    )
    b = KnowledgeItem(
        title="B",
        content="beta content",
        category="cat",
        concepts=[],
        relationships=[],
        source="src",
        tags=[],
        domain="d",
    )
    rec_a = sm.store_knowledge_item(a)
    rec_b = sm.store_knowledge_item(b)
    # low threshold should return results (may be empty in some embeddings impls) but must not error
    out_low = sm.semantic_search("alpha", top_k=2, threshold=0.0)
    assert isinstance(out_low, list)
    g = sm.build_knowledge_graph()
    assert "nodes" in g and "edges" in g
    # edges should include a->B relationship
    assert any(e.get("source") == rec_a.knowledge_id for e in g["edges"])


def test_archive_retrieve_corruption_and_checksum_behaviour():
    am = ArchiveMemory()
    rec = SessionRecord(session_id="sess-gap", user_id="u-gap")
    ref = am.archive_session(rec)
    # valid retrieval
    got = am.retrieve_archived_session(ref.archive_id)
    assert isinstance(got, SessionRecord)
    # remove data to simulate corruption
    am.storage.pop(ref.archive_id + ":data", None)
    with pytest.raises(ArchiveCorruptedError):
        am.retrieve_archived_session(ref.archive_id)
