"""Qdrant adapter interface and mock implementation for tests.
This file provides a light wrapper that the codebase can import; real PoC uses qdrant-client
but tests use MockQdrantClient below when qdrant not authorized.
"""
from __future__ import annotations
from typing import List, Dict, Any

class QdrantAdapter:
    def __init__(self, client=None):
        self.client = client

    def upsert(self, collection: str, points: List[Dict[str, Any]]) -> bool:
        if self.client is None:
            raise RuntimeError("Qdrant client not available")
        return self.client.upsert(collection, points)

    def search(self, collection: str, vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        if self.client is None:
            raise RuntimeError("Qdrant client not available")
        return self.client.search(collection, vector, top_k=top_k)


class MockQdrantClient:
    def __init__(self):
        self.storage = {}

    def upsert(self, collection: str, points: List[Dict[str, Any]]) -> bool:
        self.storage.setdefault(collection, []).extend(points)
        return True

    def search(self, collection: str, vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        items = self.storage.get(collection, [])
        # naive similarity: return first top_k
        return items[:top_k]
