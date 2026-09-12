"""Qdrant adapter: prefers qdrant-client, falls back to HTTP API.
Simple, dependency-free HTTP fallback implemented with urllib.
"""
from typing import Any, Dict, List
import json
import urllib.request
import urllib.error

QDRANT_AVAILABLE = False
_HTTP_AVAILABLE = False
_client = None
_host = 'localhost'
_port = 6333


def ensure_client(host: str = 'localhost', port: int = 6333) -> bool:
    """Try to import qdrant-client and create a client. Return True if usable."""
    global QDRANT_AVAILABLE, _client, _host, _port
    _host = host
    _port = port
    try:
        from qdrant_client import QdrantClient
        url = f'http://{host}:{port}'
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
    if QDRANT_AVAILABLE and _client is not None:
        try:
            existing = _client.get_collections()
            names = [c['name'] for c in existing.get('collections', [])] if isinstance(existing, dict) else []
            if collection_name in names:
                return True
        except Exception:
            pass
        try:
            _client.recreate_collection(collection_name=collection_name, vectors={'size': vector_size, 'distance': 'Cosine'})
            return True
        except Exception:
            try:
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
                return r.status in (200,201)
        except Exception:
            return False
    raise RuntimeError('No available Qdrant client or HTTP API')


def upsert(collection_name: str, id: str, vector: List[float], metadata: Dict[str, Any] = None) -> bool:
    """Upsert a single point via client or HTTP fallback."""
    payload = metadata if metadata is not None else {}
    if QDRANT_AVAILABLE and _client is not None:
        try:
            _client.upsert(collection_name=collection_name, points=[{'id': id, 'vector': vector, 'payload': payload}])
            return True
        except Exception as e:
            raise
    if ensure_http(_host, _port):
        body = {'points': [{'id': id, 'vector': vector, 'payload': payload}]}
        data = json.dumps(body).encode('utf-8')
        url = _http_url(f'/collections/{collection_name}/points?wait=true')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status in (200,201)
        except Exception as e:
            raise
    raise RuntimeError('Qdrant not available')


def count(collection_name: str = 'hermes_memory') -> int:
    if QDRANT_AVAILABLE and _client is not None:
        try:
            info = _client.get_collection(collection_name=collection_name)
            return int(info.get('points_count', 0)) if isinstance(info, dict) else 0
        except Exception:
            try:
                stats = _client.count(collection_name=collection_name)
                return int(stats)
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
