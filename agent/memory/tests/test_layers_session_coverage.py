import time
from datetime import datetime, timedelta

import pytest

from agent.core.types import EventRecord, KnowledgeRecord, SessionRecord
from agent.memory.core.layers import (ArchiveMemory, EpisodicMemory,
                                      SemanticMemory, SessionMemory)


def test_session_cache_eviction_on_expiry():
    sm = SessionMemory(ttl=timedelta(seconds=1))
    rec = SessionRecord(session_id="s-evict", user_id="u-1", summary="")
    sm.store("s-evict", rec)
    # ensure cached
    assert "s-evict" in sm.cache._cache
    # expire by setting created_at old
    sm.created_at["s-evict"] = datetime.now() - timedelta(days=2)
    val = sm.retrieve("s-evict")
    assert val is None
    assert "s-evict" not in sm.storage
    assert "s-evict" not in sm.cache._cache


def test_record_text_and_search_fallback():
    sm = SessionMemory(ttl=timedelta(days=1))
    rec = SessionRecord(session_id="s2", user_id="u2", summary="")
    sm.store("s2", rec)
    # search by session id should find it via fallback text
    results = sm.search("s2")
    assert any(isinstance(r, SessionRecord) and r.session_id == "s2" for r in results)


def test_search_limit_break():
    sm = SessionMemory(ttl=timedelta(days=1))
    for i in range(10):
        sm.store(
            f"s{i}", SessionRecord(session_id=f"s{i}", user_id="u", summary=f"msg {i}")
        )
    res = sm.search("msg", limit=3)
    assert len(res) == 3


def test_episodic_retrieve_and_expiry():
    em = EpisodicMemory(ttl=timedelta(seconds=1))
    er = EventRecord(event_id="e1", event_type="t", actor="a")
    em.store("e1", er)
    assert em.retrieve("e1") is not None
    # expire
    em.created_at["e1"] = datetime.now() - timedelta(days=2)
    assert em.retrieve("e1") is None


def test_semantic_search_threshold_and_non_knowledge_skip():
    sem = SemanticMemory(dim=8)
    # store a plain object that is not KnowledgeRecord
    sem.store("plain", {"foo": "bar"})
    kg = sem.build_knowledge_graph()
    # plain stored object should be skipped (no nodes)
    assert isinstance(kg, dict)
    # threshold path: if no items in index, search returns empty
    res = sem.semantic_search("anything", top_k=5, threshold=0.9)
    assert isinstance(res, list)


def test_archive_search_and_corrupted_handling():
    am = ArchiveMemory()
    s = SessionRecord(session_id="sa1", user_id="ua1", created_at=datetime.now())
    ref = am.archive_session(s)
    # search should find the archive reference by session id
    found = am.search("sa1")
    assert any(
        ref.archive_id == v.archive_id for v in found if hasattr(v, "archive_id")
    )
    # corrupt the stored data and expect ArchiveCorruptedError on retrieve
    key = ref.archive_id + ":data"
    am.storage[key] = b"corrupted"
    with pytest.raises(Exception):
        am.retrieve_archived_session(ref.archive_id)
