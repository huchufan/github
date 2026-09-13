"""
Add optional LRUCache shim to memory layers for compatibility.
"""

class LRUCache:
    def __init__(self, capacity: int = 1024):
        self.capacity = capacity
        self._store = {}

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value

