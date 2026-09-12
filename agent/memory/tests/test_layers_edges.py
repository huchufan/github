import pytest
from agent.memory.core.layers import SemanticMemory, ArchiveMemory, EpisodicMemory, SessionMemory
from agent.memory.core.embeddings import EmbeddingModel
from agent.core.types import KnowledgeItem, SessionRecord, SystemEvent
from agent.core.errors import ArchiveCorruptedError
from datetime import timedelta, datetime


def test_semantic_store_search_and_missing_index_item():
    sm = SemanticMemory(dim=64)
    item = KnowledgeItem(title='T1', content='some content about python', category='code', context='ctx')
    rec = sm.store_knowledge_item(item)
    # semantic search should find the stored item
    results = sm.semantic_search('python', top_k=5)
    assert any(r.knowledge_id == rec.knowledge_id for r in results)
    # Add a ghost id into the index that has no storage record and ensure search continues safely
    sm.semantic_index.add('ghost-id', [0.0]*sm.embedding_model.dim)
    res2 = sm.semantic_search('nothing', top_k=5)
    # should not raise and should be a list
    assert isinstance(res2, list)


def test_build_knowledge_graph_handles_missing_relationships():
    sm = SemanticMemory(dim=32)
    item = KnowledgeItem(title='A', content='alpha', category='cat', context='c')
    r = sm.store_knowledge_item(item)
    # add a fake relationship in storage to simulate edge generation
    rec = sm.storage[r.knowledge_id]
    rec.relationships = [{'target_id': 'nonexistent', 'type': 'rel', 'strength': 0.5}]
    graph = sm.build_knowledge_graph()
    assert 'nodes' in graph and 'edges' in graph


def test_archive_retrieve_corrupted_and_missing():
    am = ArchiveMemory()
    s = SessionRecord(session_id='sess-abc', user_id='u1')
    ref = am.archive_session(s)
    # retrieving works
    got = am.retrieve_archived_session(ref.archive_id)
    assert isinstance(got, SessionRecord)
    # corrupt the stored data to trigger ArchiveCorruptedError
    am.storage[ref.archive_id + ':data'] = b'corrupt'
    with pytest.raises(ArchiveCorruptedError):
        am.retrieve_archived_session(ref.archive_id)
    # unknown archive id returns None
    assert am.retrieve_archived_session('no-such-id') is None


def test_episodic_expiry_and_patterns():
    em = EpisodicMemory(ttl=timedelta(days=1))
    ev = SystemEvent(type='job', actor='a', action='run', resource='r', session_id='s', conversation_id='c', result={}, success=True)
    rec = em.record_event(ev)
    # simulate expiry
    em.created_at[rec.event_id] = datetime.now() - timedelta(days=2)
    assert em.retrieve(rec.event_id) is None


def test_session_search_and_record_text():
    sm = SessionMemory()
    sr = SessionRecord(session_id='sess-1', user_id='u9')
    sr.summary = 'Discuss python and testing'
    sr.key_decisions = ['use pytest']
    sm.store('sess-1', sr)
    results = sm.search('python', limit=10)
    assert any(isinstance(r, SessionRecord) or 'python' in str(r).lower() for r in results)
