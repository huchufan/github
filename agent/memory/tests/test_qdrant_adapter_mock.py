import pytest

from agent.memory.qdrant_adapter import QdrantAdapter, MockQdrantClient


def test_mock_qdrant_upsert_and_search():
    client = MockQdrantClient()
    adapter = QdrantAdapter(client=client)
    points = [{'id':'p1','vector':[0.1,0.2],'payload':{'text':'hello'}}]
    assert adapter.upsert('col1', points)
    res = adapter.search('col1', [0.1,0.2], top_k=1)
    assert len(res) == 1
    assert res[0]['id'] == 'p1'
