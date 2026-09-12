# migrate_to_qdrant.py
"""Migrate in_memory_store.pkl to Qdrant via qdrant_adapter.upsert

Requires qdrant_adapter.QDRANT_AVAILABLE == True and qdrant-client installed.
"""
# ensure project root on sys.path
import sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pickle
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / 'implementation' / 'memory' / 'in_memory_store.pkl'
from implementation.memory import qdrant_adapter

OUT_LOG = ROOT / 'implementation' / 'automation' / 'migrate_qdrant.log'


def load_store():
    if not STORE.exists():
        raise FileNotFoundError(STORE)
    return pickle.loads(STORE.read_bytes())


def migrate(batch_size=200):
    # Ensure either client or HTTP API is available before migrating
    client_ok = False
    try:
        client_ok = qdrant_adapter.ensure_client()
    except Exception:
        client_ok = False
    http_ok = False
    try:
        http_ok = qdrant_adapter.ensure_http()
    except Exception:
        http_ok = False
    if not (client_ok or http_ok or getattr(qdrant_adapter, 'QDRANT_AVAILABLE', False)):
        raise RuntimeError('Qdrant adapter not available; ensure qdrant-client installed or HTTP API reachable')

    # load store and infer vector size
    store = load_store()
    keys = list(store.keys())
    total = len(keys)
    i = 0
    migrated = 0
    failed = 0
    # Use collection name
    collection_name = 'hermes_memory'
    # infer vector size from first item if possible
    vector_size = None
    if total > 0:
        first_vec = store[keys[0]].get('vector') if isinstance(store[keys[0]], dict) else None
        if first_vec is not None:
            try:
                vector_size = len(first_vec)
            except Exception:
                vector_size = None
    try:
        if vector_size:
            qdrant_adapter.create_collection_if_not_exists(collection_name=collection_name, vector_size=vector_size)
        else:
            qdrant_adapter.create_collection_if_not_exists(collection_name=collection_name)
    except Exception as e:
        # ensure log file exists and write warning
        OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with OUT_LOG.open('a', encoding='utf-8') as f:
            f.write(f'WARN create_collection: {e}\n')
    import uuid
    def _normalize_id(orig_id: str) -> str:
        # Qdrant requires point IDs to be int or UUID. Normalize arbitrary strings to deterministic UUID5.
        try:
            # Accept plain ints
            int(orig_id)
            return str(orig_id)
        except Exception:
            pass
        try:
            # If already a UUID string, return it
            import uuid as _u
            _u.UUID(orig_id)
            return orig_id
        except Exception:
            # deterministic UUID5 based on NAMESPACE_OID
            return str(uuid.uuid5(uuid.NAMESPACE_OID, orig_id))

    while i < total:
        batch = keys[i:i+batch_size]
        for k in batch:
            try:
                vec = store[k]['vector']
                meta = store[k].get('metadata')
                if not isinstance(meta, dict):
                    meta = {'orig_metadata': str(meta)} if meta is not None else {}
                # preserve original id in metadata
                meta['orig_id'] = k
                pid = _normalize_id(k)
                qdrant_adapter.upsert(collection_name, pid, vec, meta)
                migrated += 1
            except Exception as e:
                failed += 1
                # capture HTTPError body if present
                err_info = None
                try:
                    import urllib.error
                    if isinstance(e, urllib.error.HTTPError):
                        try:
                            body = e.read().decode('utf-8')
                        except Exception:
                            body = '<no body available>'
                        err_info = f'HTTPError {getattr(e, "code", "?")}: {body}'
                except Exception:
                    err_info = None
                if not err_info:
                    err_info = repr(e)
                # ensure log dir
                OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
                with OUT_LOG.open('a', encoding='utf-8') as f:
                    try:
                        vec_len = len(vec) if vec is not None else 'None'
                    except Exception:
                        vec_len = 'Err'
                    meta_keys = list(meta.keys()) if isinstance(meta, dict) else type(meta)
                    f.write(f'ERROR {k} (mapped {pid}): {err_info}\n')
                    f.write(f'PAYLOAD {k}: vec_len={vec_len}, meta_keys={meta_keys}\n')
        i += batch_size
        time.sleep(0.1)
    return {'migrated': migrated, 'failed': failed}


if __name__ == '__main__':
    print('Starting migration to Qdrant...')
    print('QDRANT_AVAILABLE:', qdrant_adapter.QDRANT_AVAILABLE)
    res = migrate()
    print('Done:', res)
