#!/usr/bin/env bash
# Hermes daily progress run
set -euo pipefail
REPO_ROOT="/Users/huchufan/Hermes"
OBSIDIAN_DIR="/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes"
TS=$(date +"%Y%m%d_%H%M%S")
OUTDIR="$REPO_ROOT/implementation/automation/coverage_daily_$TS"
mkdir -p "$OUTDIR"
cd "$REPO_ROOT"

LOG="${OUTDIR}/run.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== Hermes daily progress run: $TS ==="
# 1) Run targeted tests: multiagent health monitor + memory layers
pytest -q agent/multiagent/tests/test_health_monitor.py || true
pytest -q agent/memory/tests/test_layers_* -q || true

# 2) Full coverage run (may be heavy)
python3 -m pytest -q --maxfail=1 --cov=agent --cov-report=xml:$OUTDIR/coverage.xml --cov-report=html:$OUTDIR/htmlcov || true

# 3) parse coverage xml for line-rate
PY="import xml.etree.ElementTree as ET; r=ET.parse('$OUTDIR/coverage.xml').getroot(); print(r.get('line-rate'))"
COV_RATE=$(python3 - <<PY
$PY
PY
)

# 4) write summary into Obsidian daily note
DAILY_NOTE="$OBSIDIAN_DIR/DAILY_PROGRESS_$TS.md"
cat > "$DAILY_NOTE" <<MD
# Hermes Daily Progress - $TS

- timestamp: $TS
- coverage_line_rate: $COV_RATE
- artifacts: $OUTDIR
- run_log: $LOG

MD

echo "Wrote daily note: $DAILY_NOTE"

# 5) append to a running SUMMARY.md in Obsidian
SUMMARY="$OBSIDIAN_DIR/DAILY_SUMMARY.md"
if [ ! -f "$SUMMARY" ]; then
  echo "# Hermes Daily Summary" > "$SUMMARY"
fi
echo "- $TS: coverage=$COV_RATE, artifacts=$OUTDIR" >> "$SUMMARY"

echo "Done"
