import pytest
from datetime import datetime, timedelta

from agent.memory.core.layers import (
    MemoryLayer,
    ImmediateContextMemory,
    SessionMemory,
    EpisodicMemory,
    SemanticMemory,
    ArchiveMemory,
    LRUCache,
)
from agent.core.types import SessionRecord, KnowledgeItem, KnowledgeRecord


def test_memorylayer_cleanup_expired():
    # Use a concrete MemoryLayer implementation for cleanup test (EpisodicMemory)
    em = EpisodicMemory(ttl=timedelta(seconds=1))
    em.store('k1', {'a': 1})
    # force created_at old
    em.created_at['k1'] = datetime.now() - timedelta(days=2)
    cleaned = em.cleanup_expired()
    assert cleaned >= 1
    assert 'k1' not in em.storage


def test_immediatecontext_expiry_path():
    im = ImmediateContextMemory(ttl=timedelta(seconds=1))
    im.store('x', 'v')
    assert im.retrieve('x') == 'v'
    # force expiry
    im.created_at['x'] = datetime.now() - timedelta(days=2)
    assert im.retrieve('x') is None


def test_episdodic_expiry_and_search():
    em = EpisodicMemory(ttl=timedelta(seconds=1))
    em.store('e1', 'hello world')
    assert em.retrieve('e1') == 'hello world'
    # search should find
    res = em.search('hello')
    assert any('hello' in str(r) for r in res)
    # expire
    em.created_at['e1'] = datetime.now() - timedelta(days=100)
    assert em.retrieve('e1') is None


def test_semantic_store_search_and_graph_edges():
    sm = SemanticMemory(dim=8)
    item = KnowledgeItem(title='NodeA', content='content A', category='cat', concepts=[], relationships=[{'target_id':'idB','type':'rel','strength':2.0}], source='src', tags=[], domain='d')
    rec = sm.store_knowledge_item(item)
    # semantic_search low threshold should return something (or at least not error)
    out = sm.semantic_search('content', top_k=1, threshold=0.0)
    assert isinstance(out, list)
    g = sm.build_knowledge_graph()
    assert 'nodes' in g and 'edges' in g
    # ensure relationships produced edges
    assert any(edge.get('source') == rec.knowledge_id for edge in g['edges'])


def test_archive_retrieve_corruption_and_checksum():
    am = ArchiveMemory()
    rec = SessionRecord(session_id='sessX', user_id='uX')
    ref = am.archive_session(rec)
    # tamper storage to trigger corruption
    am.storage[ref.archive_id + ':data'] = b'corrupt'
    with pytest.raises(Exception):
        am.retrieve_archived_session(ref.archive_id)
