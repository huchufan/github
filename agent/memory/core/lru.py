"""
LRU cache compatibility shim for memory layers tests.
Provides a small LRUCache compatible with tests that expect:
- constructor accepts size=... (alias for capacity)
- methods: put(key, value), get(key, default=None)
- containment: 'key in cache' checks presence
- LRU eviction when capacity exceeded

This is a minimal PoC implementation using OrderedDict.
"""
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    def __init__(self, capacity: Optional[int] = None, size: Optional[int] = None):
        """Initialize LRUCache.

        Backwards-compatible: caller may pass size=NN (tests) or capacity=NN.
        If neither provided, default to 1024.
        """
        if size is not None:
            self.capacity = int(size)
        elif capacity is not None:
            self.capacity = int(capacity)
        else:
            self.capacity = 1024
        self._store = OrderedDict()

    # compatibility: test expects put()/get()
    def put(self, key: Any, value: Any) -> None:
        # insert or update, move to end as most-recently-used
        if key in self._store:
            # update value and mark as recently used
            self._store.pop(key)
        self._store[key] = value
        # evict least-recently-used if over capacity
        while len(self._store) > self.capacity:
            self._store.popitem(last=False)

    def set(self, key: Any, value: Any) -> None:
        # alias to put
        self.put(key, value)

    def get(self, key: Any, default: Any = None) -> Any:
        if key not in self._store:
            return default
        # move to end and return
        val = self._store.pop(key)
        self._store[key] = val
        return val

    def __contains__(self, key: Any) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()
