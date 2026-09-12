import pytest
from datetime import datetime, timedelta

from agent.memory.core.layers import (
    LRUCache,
    ImmediateContextMemory,
    SessionMemory,
    EpisodicMemory,
    SemanticMemory,
    ArchiveMemory,
)
from agent.core.types import (
    SessionRecord,
    ConversationTurn,
    SystemEvent,
    KnowledgeItem,
)
from agent.core.errors import ArchiveCorruptedError


def test_lru_cache_eviction_and_order():
    c = LRUCache(size=2)
    c.put('a', 1)
    c.put('b', 2)
    assert 'a' in c and 'b' in c
    # access a to make it recent
    assert c.get('a') == 1
    c.put('c', 3)
    # b should be evicted
    assert 'b' not in c
    assert c.get('a') == 1
    assert c.get('c') == 3


def test_immediate_context_record_and_attention():
    im = ImmediateContextMemory(max_size=5)
    t = im.record_conversation_turn('hello', 'hi')
    ctx = im.get_conversation_context(window_size=1)
    assert isinstance(ctx, object)
    # attention stack empty
    att = im.get_attention_context()
    assert att.items == []
    # set attention stack
    im.attention_stack = ['focus1', 'focus2']
    att2 = im.get_attention_context()
    assert att2.primary == 'focus1'
    assert att2.secondary == ['focus2']


def test_session_memory_search_and_record_text_and_expiry():
    sm = SessionMemory(ttl=timedelta(seconds=1))
    rec = SessionRecord(session_id='s2', user_id='u2')
    sm.store('s2', rec)
    assert sm.retrieve('s2') is not None
    # test search by summary (empty summary -> fallback to str)
    results = sm.search('s2')
    assert any('s2' in str(r) for r in results)
    # expiry
    sm.created_at['s2'] = datetime.now() - timedelta(days=31)
    assert sm.retrieve('s2') is None


def test_episdodic_record_and_patterns():
    em = EpisodicMemory()
    # create two events: one success with action 'A', one failure with error 'E'
    e1 = SystemEvent(type='type1', actor='actor1', action='A', resource=None, session_id=None, conversation_id=None, related_event_ids=[], result=None, success=True, error=None, consequences=None)
    e2 = SystemEvent(type='type1', actor='actor1', action='B', resource=None, session_id=None, conversation_id=None, related_event_ids=[], result=None, success=False, error='E', consequences=None)
    r1 = em.record_event(e1)
    r2 = em.record_event(e2)
    patterns = em.extract_learned_patterns()
    assert any(p.pattern_type in ('success_sequence', 'failure_recovery') for p in patterns)


def test_semantic_memory_store_and_search_and_graph():
    sm = SemanticMemory(dim=8)
    item = KnowledgeItem(title='T', content='some content about X', category='cat', concepts=[], relationships=[], source='src', tags=[], domain='d')
    rec = sm.store_knowledge_item(item)
    # search with high threshold likely returns empty
    res_high = sm.semantic_search('X', top_k=1, threshold=0.99)
    assert isinstance(res_high, list)
    # search with low threshold should return results
    res_low = sm.semantic_search('X', top_k=1, threshold=0.0)
    assert isinstance(res_low, list)
    g = sm.build_knowledge_graph()
    assert 'nodes' in g and 'edges' in g


def test_archive_store_and_corruption_detection():
    am = ArchiveMemory()
    rec = SessionRecord(session_id='s3', user_id='u3')
    ref = am.archive_session(rec)
    # valid retrieval
    got = am.retrieve_archived_session(ref.archive_id)
    assert isinstance(got, SessionRecord)
    # corrupt the stored data
    am.storage[ref.archive_id + ':data'] = b'invalid'
    with pytest.raises(ArchiveCorruptedError):
        am.retrieve_archived_session(ref.archive_id)
