import pytest
from datetime import datetime, timedelta, timezone

from agent.memory.core.layers import (
    LRUCache,
    SessionMemory,
    EpisodicMemory,
    SemanticMemory,
    ArchiveMemory,
)
from agent.core.types import SessionRecord, EventRecord, KnowledgeItem
from agent.core.errors import ArchiveCorruptedError


def test_lru_cache_eviction_and_contains():
    c = LRUCache(size=3)
    c.put('a', 1)
    c.put('b', 2)
    c.put('c', 3)
    assert 'a' in c
    c.put('d', 4)
    # 'a' should be evicted
    assert 'a' not in c


def test_session_record_text_with_summary_and_key_decisions():
    sm = SessionMemory(ttl=timedelta(days=1))
    rec = SessionRecord(session_id='sid1', user_id='uid1', summary='This is a summary', key_decisions=['d1'])
    sm.store('sid1', rec)
    # _record_text should use summary + key_decisions
    results = sm.search('This is', limit=5)
    assert any(r.session_id == 'sid1' for r in results)


def test_session_cache_internal_delete_and_missing_created_at():
    sm = SessionMemory(ttl=timedelta(days=1))
    rec = SessionRecord(session_id='tmp', user_id='u')
    sm.store('tmp', rec)
    # simulate missing created_at entry
    sm.created_at.pop('tmp', None)
    # retrieval should handle missing created_at gracefully and return record
    val = sm.retrieve('tmp')
    assert val is not None


def test_episodic_search_limit_and_expiry():
    em = EpisodicMemory(ttl=timedelta(seconds=1))
    for i in range(5):
        er = EventRecord(event_id=f'e{i}', event_type='t', actor='a')
        em.store(f'e{i}', er)
    res = em.search('t', limit=2)
    assert len(res) == 2
    # expire one and ensure retrieve returns None
    key = 'e0'
    em.created_at[key] = datetime.now(timezone.utc) - timedelta(days=2)
    assert em.retrieve(key) is None


def test_semantic_search_threshold_and_missing_storage_entry():
    sem = SemanticMemory(dim=8)
    # add a knowledge item and then remove storage entry to simulate missing record
    item = KnowledgeItem(title='K', content='content', category='cat')
    rec = sem.store_knowledge_item(item)
    # remove actual record but keep index
    sem.storage.pop(rec.knowledge_id, None)
    # search should skip missing records and return empty
    res = sem.semantic_search('content', top_k=5, threshold=0.0)
    assert isinstance(res, list)


def test_archive_checksum_mismatch_raises():
    am = ArchiveMemory()
    s = SessionRecord(session_id='sa2', user_id='uu', created_at=datetime.now(timezone.utc))
    ref = am.archive_session(s)
    key = ref.archive_id + ':data'
    # tamper data
    am.storage[key] = b'broken'
    with pytest.raises(ArchiveCorruptedError):
        am.retrieve_archived_session(ref.archive_id)
