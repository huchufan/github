from datetime import datetime, timedelta

import pytest

from agent.core.errors import ArchiveCorruptedError
from agent.core.types import KnowledgeItem, SessionRecord
from agent.memory.core.layers import (ArchiveMemory, ImmediateContextMemory,
                                      LRUCache, SemanticMemory, SessionMemory)


def test_lrucache_put_move_and_eviction():
    c = LRUCache(size=2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c and "b" in c
    # re-put a should move it to end so b is least-recent
    c.put("a", 1)
    c.put("c", 3)
    assert "b" not in c
    assert "a" in c and "c" in c


def test_immediatecontext_search_and_expiry():
    im = ImmediateContextMemory(max_size=5, ttl=timedelta(seconds=1))
    im.store("k1", {"note": "hello world"})
    assert im.retrieve("k1") is not None
    # search should match
    res = im.search("hello")
    assert any("hello" in str(r) for r in res)
    # expire
    im.created_at["k1"] = datetime.now() - timedelta(days=2)
    assert im.retrieve("k1") is None


def test_sessionmemory_cache_expiry_cleans_internal_cache():
    sm = SessionMemory(ttl=timedelta(seconds=1))
    rec = SessionRecord(session_id="sessX", user_id="uX")
    sm.store("sessX", rec)
    assert sm.retrieve("sessX") is not None
    # simulate expiry
    sm.created_at["sessX"] = datetime.now() - timedelta(days=31)
    got = sm.retrieve("sessX")
    assert got is None
    # internal cache should not contain key
    internal = getattr(sm.cache, "_cache", {})
    assert "sessX" not in internal


def test_semantic_search_threshold_and_retrieve():
    sm = SemanticMemory(dim=8)
    item = KnowledgeItem(
        title="Alpha",
        content="alpha content about X",
        category="cat",
        concepts=[],
        relationships=[],
        source="src",
        tags=[],
        domain="d",
    )
    rec = sm.store_knowledge_item(item)
    # retrieve should return record
    got = sm.retrieve(rec.knowledge_id)
    assert got is not None
    # high threshold likely returns empty but must not error
    out_high = sm.semantic_search("alpha", top_k=1, threshold=0.99)
    assert isinstance(out_high, list)
    out_low = sm.semantic_search("alpha", top_k=1, threshold=0.0)
    assert isinstance(out_low, list)


def test_archive_retrieve_corruption_detection_and_checksum():
    am = ArchiveMemory()
    rec = SessionRecord(session_id="sarch", user_id="uarch")
    ref = am.archive_session(rec)
    # valid retrieval
    got = am.retrieve_archived_session(ref.archive_id)
    assert isinstance(got, SessionRecord)
    # remove stored data to simulate corruption
    am.storage.pop(ref.archive_id + ":data", None)
    with pytest.raises(ArchiveCorruptedError):
        am.retrieve_archived_session(ref.archive_id)
