"""Qdrant adapter: prefers qdrant-client, falls back to HTTP API.
Simple, dependency-free HTTP fallback implemented with urllib.
This file was patched to: (1) initialize client when possible, (2) robustly parse client results,
(3) normalize point ids (UUID/int) for HTTP fallback, and (4) expose deterministic id helper.
"""
from typing import Any, Dict, List
import json
import urllib.request
import urllib.error
import uuid

QDRANT_AVAILABLE = False
_HTTP_AVAILABLE = False
_client = None
_host = 'localhost'
_port = 6333


def _normalize_id(pid: Any) -> Any:
    """Ensure the id passed to Qdrant is either an int or a UUID string.
    If pid is an int -> return as-is. If pid is a UUID string -> return as-is.
    Otherwise return a deterministic UUID5 based on the string representation.
    """
    if isinstance(pid, int):
        return pid
    try:
        # allow already-valid UUID string
        u = uuid.UUID(str(pid))
        return str(u)
    except Exception:
        # return deterministic UUID5 derived from namespace URL and the pid string
        return str(uuid.uuid5(uuid.NAMESPACE_URL, str(pid)))


def ensure_client(host: str = 'localhost', port: int = 6333) -> bool:
    """Try to import qdrant-client and create a client. Return True if usable."""
    global QDRANT_AVAILABLE, _client, _host, _port
    _host = host
    _port = port
    try:
        from qdrant_client import QdrantClient
        url = f'http://{host}:{port}'
        # Prefer an explicit client URL constructor
        _client = QdrantClient(url=url)
        QDRANT_AVAILABLE = True
        return True
    except Exception:
        QDRANT_AVAILABLE = False
        _client = None
        return False


def ensure_http(host: str = 'localhost', port: int = 6333, timeout: float = 2.0) -> bool:
    """Check HTTP /collections endpoint. Return True if reachable."""
    global _HTTP_AVAILABLE, _host, _port
    _host = host
    _port = port
    try:
        url = f'http://{host}:{port}/collections'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status == 200:
                _HTTP_AVAILABLE = True
                return True
    except Exception:
        _HTTP_AVAILABLE = False
    return False


def _http_url(path: str) -> str:
    return f'http://{_host}:{_port}{path}'


def create_collection_if_not_exists(collection_name: str = 'hermes_memory', vector_size: int = 1536) -> bool:
    """Create collection via client if available, else via HTTP PUT /collections/{name}.
    Returns True on success or if already exists.
    """
    # Prefer client API and handle returned types robustly
    if QDRANT_AVAILABLE and _client is not None:
        try:
            existing = _client.get_collections()
            # existing may be a dict with 'collections' key or an object with .collections
            names = []
            if isinstance(existing, dict):
                names = [c.get('name') for c in existing.get('collections', [])]
            else:
                # object with .collections attribute
                coll = getattr(existing, 'collections', None)
                if coll is None:
                    # try iterating if it's list-like
                    try:
                        names = [c.name for c in existing]
                    except Exception:
                        names = []
                else:
                    try:
                        names = [c.name for c in coll]
                    except Exception:
                        names = []
            if collection_name in (names or []):
                return True
        except Exception:
            pass
        try:
            # try client recreate/create
            try:
                _client.recreate_collection(collection_name=collection_name, vectors={'size': vector_size, 'distance': 'Cosine'})
            except Exception:
                _client.create_collection(collection_name=collection_name, vectors={'size': vector_size, 'distance': 'Cosine'})
            return True
        except Exception:
            pass
    # HTTP fallback
    if ensure_http(_host, _port):
        # check exists
        try:
            req = urllib.request.Request(_http_url(f'/collections/{collection_name}'), method='GET')
            with urllib.request.urlopen(req, timeout=3) as r:
                if r.status == 200:
                    return True
        except urllib.error.HTTPError as e:
            if e.code != 404:
                # other error
                pass
        except Exception:
            pass
        # create
        payload = {'vectors': {'size': vector_size, 'distance': 'Cosine'}}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(_http_url(f'/collections/{collection_name}'), data=data, headers={'Content-Type': 'application/json'}, method='PUT')
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status in (200, 201)
        except Exception:
            return False
    raise RuntimeError('No available Qdrant client or HTTP API')


def upsert(collection_name: str, id: Any, vector: List[float], metadata: Dict[str, Any] = None) -> bool:
    """Upsert a single point via client or HTTP fallback. Normalizes id to UUID/int for Qdrant."""
    payload = metadata if metadata is not None else {}
    nid = _normalize_id(id)
    if QDRANT_AVAILABLE and _client is not None:
        try:
            # qdrant-client accepts PointStruct or dicts; prefer using client models when possible
            try:
                from qdrant_client.http.models import PointStruct
                point = PointStruct(id=nid, vector=vector, payload=payload)
                _client.upsert(collection_name=collection_name, points=[point])
            except Exception:
                # fallback to dict form
                _client.upsert(collection_name=collection_name, points=[{'id': nid, 'vector': vector, 'payload': payload}])
            return True
        except Exception as e:
            raise
    if ensure_http(_host, _port):
        # HTTP API requires UUID or integer ids; nid is normalized to a UUID string when necessary
        body = {'points': [{'id': nid, 'vector': vector, 'payload': payload}]}
        data = json.dumps(body).encode('utf-8')
        url = _http_url(f'/collections/{collection_name}/points?wait=true')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status in (200, 201)
        except Exception as e:
            raise
    raise RuntimeError('Qdrant not available')


def count(collection_name: str = 'hermes_memory') -> int:
    """Return number of points in collection using client when available, else HTTP info endpoint."""
    if QDRANT_AVAILABLE and _client is not None:
        try:
            # preferred: use client.count() which returns a Count object or similar
            stats = _client.count(collection_name=collection_name)
            # stats may be object with attribute 'count' or integer or dict
            if hasattr(stats, 'count'):
                try:
                    return int(stats.count)
                except Exception:
                    pass
            if isinstance(stats, dict):
                return int(stats.get('count', 0))
            # last resort
            return int(stats)
        except Exception:
            try:
                info = _client.get_collection(collection_name=collection_name)
                # info may be object with points_count attribute
                pc = getattr(info, 'points_count', None)
                if pc is not None:
                    return int(pc)
                # dict-like
                if isinstance(info, dict):
                    return int(info.get('points_count', 0) or info.get('indexed_vectors_count', 0) or 0)
            except Exception:
                return 0
    if ensure_http(_host, _port):
        try:
            req = urllib.request.Request(_http_url(f'/collections/{collection_name}/info'), method='GET')
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    data = json.loads(r.read().decode('utf-8'))
                    res = data.get('result', {})
                    return int(res.get('vectors_count') or res.get('points_count') or 0)
        except Exception:
            return 0
    raise RuntimeError('Qdrant not available')


# Try to initialize client on import to prefer client over HTTP fallback
try:
    ensure_client(_host, _port)
except Exception:
    pass

