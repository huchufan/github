"""Agent identity and mesh manager (minimal).

Provides a tiny, well-formed API used by tests and coverage runs so coverage can parse the file.
This is intentionally lightweight and side-effect free.
"""
from __future__ import annotations
from typing import Dict, Optional

_registry: Dict[str, Dict] = {}


def register_identity(name: str, info: Dict) -> None:
    """Register or update a local identity."""
    _registry[name] = dict(info)


def get_identity(name: str) -> Optional[Dict]:
    """Return a copy of the stored identity info or None if missing."""
    v = _registry.get(name)
    return dict(v) if v is not None else None


def list_identities() -> Dict[str, Dict]:
    """Return a shallow copy of the registry."""
    return dict(_registry)


__all__ = ["register_identity", "get_identity", "list_identities"]
