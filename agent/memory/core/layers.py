"""
Memory Framework - Layers Module (compat shim)
Provides MemoryLayer base, ImmediateContextMemory and a small SemanticMemory stub used by tests and benchmark.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

class MemoryLayer:
    """Base memory layer interface"""
    def __init__(self, name: str, ttl: Optional[timedelta] = None):
        self.name = name
        self.ttl = ttl
        self.storage: Dict[str, Any] = {}
        self.created_at: Dict[str, datetime] = {}

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def store(self, key: str, value: Any) -> None:
        self.storage[key] = value
        self.created_at[key] = self.now()

    def retrieve(self, key: str) -> Optional[Any]:
        if key not in self.storage:
            return None
        if self.ttl and (self.now() - self.created_at[key]) > self.ttl:
            del self.storage[key]
            del self.created_at[key]
            return None
        return self.storage[key]

    def search(self, query: str, limit: int = 10) -> List[Any]:
        results: List[Any] = []
        for k, v in self.storage.items():
            if query.lower() in str(v).lower():
                results.append(v)
                if len(results) >= limit:
                    break
        return results

class ImmediateContextMemory(MemoryLayer):
    def __init__(self):
        super().__init__("immediate", ttl=timedelta(hours=2))

class SemanticMemory(MemoryLayer):
    """Stub semantic memory for embeddings-backed storage (mocked for tests)
    Provides index and query semantics but stores plain values for PoC.
    """
    def __init__(self):
        super().__init__("semantic", ttl=None)
        # simple list index
        self.index: List[Dict[str, Any]] = []

    def index_item(self, id: str, vector: List[float], payload: Any):
        self.index.append({"id": id, "vector": vector, "payload": payload})

    def query_vector(self, vector: List[float], top_k: int = 5) -> List[Any]:
        # PoC: return first top_k payloads
        return [e['payload'] for e in self.index[:top_k]]

__all__ = ["MemoryLayer", "ImmediateContextMemory", "SemanticMemory"]
