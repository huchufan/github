#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BACKUP_DIR="$ROOT/implementation/automation/backups"
mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d_%H%M%S)
OUT_JSONL="$BACKUP_DIR/hermes_memory_points_${TS}.jsonl"
OUT_COLS="$BACKUP_DIR/qdrant_collections_${TS}.json"
OUT_COLS_SHA="$OUT_COLS.sha256"
# export points via qdrant_client Python script
python3 - <<PY
from qdrant_client import QdrantClient
import json, sys
client=QdrantClient(None, port=6333)
count=client.count('hermes_memory')
print('client count', count)
with open(r"$OUT_JSONL", 'w', encoding='utf-8') as f:
    for batch in client.scroll(collection_name='hermes_memory', limit=500):
        for rec in batch:
            try:
                f.write(json.dumps({'id': rec.id, 'payload': rec.payload}) + "\n")
            except Exception:
                pass
# dump collections list
cols = client.get_collections()
with open(r"$OUT_COLS", 'w', encoding='utf-8') as f:
    f.write(json.dumps(cols, indent=2))
PY
# compute sha256
if [ -f "$OUT_JSONL" ]; then
  shasum -a 256 "$OUT_JSONL" | awk '{print $1}' > "$OUT_JSONL.sha256"
fi
if [ -f "$OUT_COLS" ]; then
  shasum -a 256 "$OUT_COLS" | awk '{print $1}' > "$OUT_COLS_SHA"
fi
# rotate: keep last 7 backups
ls -1t "$BACKUP_DIR"/hermes_memory_points_*.jsonl 2>/dev/null | sed -n '8,$p' | xargs -r rm -f
ls -1t "$BACKUP_DIR"/qdrant_collections_*.json 2>/dev/null | sed -n '8,$p' | xargs -r rm -f

echo "WROTE $OUT_JSONL"