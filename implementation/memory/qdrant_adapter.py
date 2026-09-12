"""Qdrant adapter with qdrant-client and HTTP fallback.
Provides:
 - ensure_client(host,port)
 - ensure_http(host,port)
 - create_collection_if_not_exists(collection_name, vector_size)
 - upsert(collection_name, id, vector, metadata)
 - count(collection_name)

Behavior: prefer qdrant-client if available; otherwise use HTTP API.
"""
from typing import Any, Dict, List
import json
import time

QDRANT_AVAILABLE = False
_HTTP_AVAILABLE = False
_client = None
_host = 'localhost'
_port = 6333


def ensure_client(host: str = 'localhost', port: int = 6333):
    """Try to import qdrant-client and connect. Returns True if client usable."""
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


def ensure_http(host: str = 'localhost', port: int = 6333, timeout: float = 2.0):
    """Check HTTP API /collections endpoint. Returns True if reachable."""
    global _HTTP_AVAILABLE, _host, _port
    _host = host
    _port = port
    try:
        import http.client
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request('GET', '/collections')
        resp = conn.getresponse()
        data = resp.read(1024)
        conn.close()
        if resp.status == 200:
            _HTTP_AVAILABLE = True
            return True
    except Exception:
        _HTTP_AVAILABLE = False
    return False


def _http_url(path: str):
    return f'http://{_host}:{_port}{path}'


def create_collection_if_not_exists(collection_name: str = 'hermes_memory', vector_size: int = 1536):
    if QDRANT_AVAILABLE and _client is not None:
        # try client methods
        try:
            existing = _client.get_collections()
            names = [c['name'] for c in existing.get('collections', [])] if isinstance(existing, dict) else []
        except Exception:
            names = []
        if collection_name in names:
            return True
        try:
            # try recreate then create
            _client.recreate_collection(collection_name=collection_name, vectors={'size': vector_size, 'distance': 'Cosine'})
            return True
        except Exception:
            try:
                _client.create_collection(collection_name=collection_name, vectors={'size': vector_size, 'distance': 'Cosine'})
                return True
            except Exception:
                raise
    # HTTP fallback
    if _HTTP_AVAILABLE:
        try:
            import urllib.request
            url = _http_url(f"/collections/{collection_name}")
            # check exists
            req = urllib.request.Request(_http_url(f"/collections/{collection_name}"), method='GET')
            try:
                with urllib.request.urlopen(req, timeout=2) as r:
                    if r.status == 200:
                        return True
            except Exception:
                pass
            # create collection
            payload = {
                'vectors': {'size': vector_size, 'distance': 'Cosine'}
            }
            req = urllib.request.Request(_http_url(f"/collections/{collection_name}"), data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='PUT')
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status in (200,201)
        except Exception:
            raise
    raise RuntimeError('No available Qdrant client or HTTP API')


def upsert(collection_name: str, id: str, vector: List[float], metadata: Dict[str, Any] = None):
    """Upsert a single point via client or HTTP fallback."""
    payload = metadata if metadata is not None else {}
    if QDRANT_AVAILABLE and _client is not None:
        try:
            _client.upsert(collection_name=collection_name, points=[{'id': id, 'vector': vector, 'payload': payload}])
            return True
        except Exception as e:
            raise
    if _HTTP_AVAILABLE:
        try:
            import urllib.request
            body = {'points': [{'id': id, 'vector': vector, 'payload': payload}]}
            data = json.dumps(body).encode('utf-8')
            req = urllib.request.Request(_http_url(f"/collections/{collection_name}/points?wait=true"), data=data, headers={'Content-Type': 'application/json'}, method='PUT')
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status in (200,201)
        except Exception as e:
            raise
    raise RuntimeError('Qdrant not available')


def count(collection_name: str = 'hermes_memory'):
    if QDRANT_AVAILABLE and _client is not None:
        try:
            info = _client.get_collection(collection_name=collection_name)
            return info.get('points_count', None) if isinstance(info, dict) else None
        except Exception:
            try:
                stats = _client.count(collection_name=collection_name)
                return stats
            except Exception:
                return None
    if _HTTP_AVAILABLE:
        try:
            import urllib.request
            req = urllib.request.Request(_http_url(f"/collections/{collection_name}/info"), method='GET')
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    data = json.loads(r.read().decode('utf-8'))
                    # data may have result.vectors_count or result.points_count
                    res = data.get('result', {})
                    return res.get('vectors_count') or res.get('points_count') or 0
        except Exception:
            return None
    raise RuntimeError('Qdrant not available')
