#!/usr/bin/env python3
"""Idempotent restore script for Qdrant: normalize IDs to UUID5, batch upsert.
Writes a report to backups/restore_full_idempotent_<ts>.md
"""
import os, time, json, hashlib, sys
from uuid import uuid5, NAMESPACE_URL
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Fix path resolution: script lives in <repo>/implementation/automation
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKUP_DIR = os.path.join(ROOT, 'implementation', 'automation', 'backups')

files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('hermes_memory_points_') and f.endswith('.jsonl')]
files.sort()
if not files:
    print('NO_JSONL')
    sys.exit(1)

VECTOR_SIZE = 128
COL = 'hermes_memory_restore'
client = QdrantClient(None, port=6333)

# ensure collection exists (HTTP fallback handled by earlier helper)
try:
    client.create_collection(collection_name=COL, vectors={'size':VECTOR_SIZE,'distance':'Cosine'})
except Exception:
    pass
# wait a bit
start = time.time(); ready = False
while time.time() - start < 30:
    try:
        cols = client.get_collections()
        names = [c['name'] for c in cols.get('collections',[])] if isinstance(cols, dict) else [c.name for c in cols.collections]
        if COL in names:
            ready = True; break
    except Exception:
        pass
    time.sleep(1)

REPORT = os.path.join(BACKUP_DIR, f'restore_full_idempotent_{int(time.time())}.md')
BATCH = 200
processed = 0
upserted = 0
failed_batches = 0
log_lines = []
ids_set = set()

# deterministic namespace for UUID5 to keep reproducible mapping
NS = NAMESPACE_URL

for fname in files:
    path = os.path.join(BACKUP_DIR, fname)
    print('processing', path)
    with open(path, 'r', encoding='utf-8') as f:
        batch = []
        for line in f:
            try:
                obj = json.loads(line)
            except Exception as e:
                log_lines.append(f'json load err: {e}')
                continue
            orig_id = obj.get('id')
            payload = obj.get('payload', {}) or {}
            # deterministic UUID5 mapping
            try:
                newid = str(uuid5(NS, str(orig_id)))
            except Exception:
                newid = str(uuid5(NS, json.dumps(obj.get('payload', {}))))
            # preserve original id in payload if not present
            if 'orig_id' not in payload:
                payload['orig_id'] = orig_id
            point = models.PointStruct(id=newid, vector=[0.0]*VECTOR_SIZE, payload=payload)
            batch.append(point)
            processed += 1
            if len(batch) >= BATCH:
                success = False
                for attempt in range(3):
                    try:
                        client.upsert(collection_name=COL, points=batch)
                        upserted += len(batch)
                        success = True
                        log_lines.append(f'upsert batch ok {upserted}')
                        break
                    except Exception as e:
                        log_lines.append(f'upsert attempt {attempt} err: {e}')
                        time.sleep(1)
                if not success:
                    failed_batches += 1
                    log_lines.append('batch failed after retries')
                batch = []
        # final
        if batch:
            success = False
            for attempt in range(3):
                try:
                    client.upsert(collection_name=COL, points=batch)
                    upserted += len(batch)
                    success = True
                    log_lines.append(f'upsert final ok {upserted}')
                    break
                except Exception as e:
                    log_lines.append(f'final upsert attempt {attempt} err: {e}')
                    time.sleep(1)
            if not success:
                failed_batches += 1
                log_lines.append('final batch failed')

# verify
try:
    cnt = client.count(COL)
except Exception as e:
    cnt = f'count_error: {e}'

ids = set()
try:
    for batch_s in client.scroll(collection_name=COL, limit=1000):
        for r in batch_s:
            try:
                rid = r.id
            except Exception:
                # r may be dict
                rid = r.get('id') if isinstance(r, dict) else str(r)
            ids.add(str(rid))
except Exception as e:
    log_lines.append(f'scroll error: {e}')

# sample check
sample_total = min(200, processed)
sample_ok = 0
missing_sample = []
# collect sample originals from first file
sample_ids = []
with open(os.path.join(BACKUP_DIR, files[0]), 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= sample_total: break
        try:
            obj = json.loads(line)
            sample_ids.append(obj.get('id'))
        except:
            pass
for sid in sample_ids:
    nid = str(uuid5(NS, str(sid)))
    if nid in ids:
        sample_ok += 1
    else:
        missing_sample.append(str(sid))

# write report
lines = []
lines.append('# restore full idempotent report')
lines.append('ts: ' + time.strftime('%Y-%m-%d %H:%M:%S'))
lines.append(f'files_processed: {len(files)}')
lines.append(f'processed_lines: {processed}')
lines.append(f'upserted: {upserted}')
lines.append(f'failed_batches: {failed_batches}')
lines.append(f'restored_count: {cnt}')
lines.append(f'scrolled_ids_count: {len(ids)}')
lines.append(f'sample_total: {sample_total}, sample_ok: {sample_ok}')
if missing_sample:
    lines.append('missing_preview:' + ','.join(missing_sample[:20]))
lines.extend(['', '# upsert log:'] + log_lines)
# sha256 of concatenated files
h = hashlib.sha256()
for fname in files:
    with open(os.path.join(BACKUP_DIR, fname), 'rb') as f:
        while True:
            b = f.read(8192)
            if not b: break
            h.update(b)
lines.append('combined_jsonl_sha256:' + h.hexdigest())
open(REPORT, 'w', encoding='utf-8').write('\n'.join(lines))
print('WROTE', REPORT)
print('processed=', processed, 'upserted=', upserted, 'failed_batches=', failed_batches, 'restored_count=', cnt)
