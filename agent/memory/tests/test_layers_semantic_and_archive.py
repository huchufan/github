import pytest
from agent.memory.core.layers import SemanticMemory, ArchiveMemory, KnowledgeItem, SessionRecord
from datetime import datetime, timedelta


def test_semantic_store_and_search_and_graph():
    sm = SemanticMemory(dim=16)
    item = KnowledgeItem(title='T', content='some content about AI', category='ai', concepts=['ai'])
    rec = sm.store_knowledge_item(item)
    assert rec.knowledge_id in sm.storage
    res = sm.semantic_search('AI', top_k=5)
    assert any(r.knowledge_id == rec.knowledge_id for r in res)
    kg = sm.build_knowledge_graph()
    assert isinstance(kg, dict)


def test_archive_store_and_retrieve_session():
    am = ArchiveMemory()
    s = SessionRecord(session_id='s1', user_id='u1', created_at=datetime.now())
    ref = am.archive_session(s)
    assert ref.archive_id in am.storage
    s2 = am.retrieve_archived_session(ref.archive_id)
    assert s2.session_id == s.session_id
