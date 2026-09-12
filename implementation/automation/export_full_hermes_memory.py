#!/usr/bin/env python3
import os, time, json
from qdrant_client import QdrantClient
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKUP_DIR=os.path.join(ROOT, 'implementation', 'automation', 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
TS=time.strftime('%Y%m%d_%H%M%S')
OUT=os.path.join(BACKUP_DIR, f'hermes_memory_points_full_{TS}.jsonl')
client=QdrantClient(None, port=6333)
print('client.count->', client.count('hermes_memory'))
with open(OUT, 'w', encoding='utf-8') as f:
    for batch in client.scroll(collection_name='hermes_memory', limit=500):
        for rec in batch:
            try:
                # rec may be object with .id/.payload or dict
                rid = getattr(rec, 'id', None) or rec.get('id')
                payload = getattr(rec, 'payload', None) or rec.get('payload', {})
                line = json.dumps({'id': rid, 'payload': payload}, ensure_ascii=False)
                f.write(line + '\n')
            except Exception as e:
                try:
                    f.write(json.dumps({'id': str(getattr(rec,'id', None) or rec.get('id')), 'payload': {}}) + '\n')
                except Exception:
                    pass
print('wrote', OUT)
