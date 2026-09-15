#!/usr/bin/env bash
# Hermes daily progress run with improved error handling
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

# Initialize counters
TASK_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# 1) Run targeted tests: multiagent health monitor
echo "[Task 1] Multiagent health monitor tests..."
TASK_COUNT=$((TASK_COUNT+1))
if python3 -m pytest -q agent/multiagent/tests/test_health_monitor.py --tb=line 2>&1 | head -50; then
    PASS_COUNT=$((PASS_COUNT+1))
    echo "✓ Task 1 passed"
else
    FAIL_COUNT=$((FAIL_COUNT+1))
    echo "✗ Task 1 failed"
fi

# 2) Run memory layer tests using pytest discovery (fixes C-001 wildcard issue)
echo "[Task 2] Memory layer tests..."
TASK_COUNT=$((TASK_COUNT+1))
if python3 -m pytest -q agent/memory/tests -k "test_layers" --tb=line 2>&1 | head -50; then
    PASS_COUNT=$((PASS_COUNT+1))
    echo "✓ Task 2 passed"
else
    FAIL_COUNT=$((FAIL_COUNT+1))
    echo "✗ Task 2 failed"
fi

# 3) Full coverage run (may be heavy) — execute only if targeted tests passed
echo "[Task 3] Full test coverage (conditional)..."
TASK_COUNT=$((TASK_COUNT+1))
if [ "$FAIL_COUNT" -eq 0 ]; then
    if python3 -m pytest -q --maxfail=5 --cov=agent --cov-report=xml:$OUTDIR/coverage.xml --cov-report=html:$OUTDIR/htmlcov 2>&1 | tee /tmp/coverage_run.out | head -100; then
        PASS_COUNT=$((PASS_COUNT+1))
        echo "✓ Task 3 passed"
    else
        FAIL_COUNT=$((FAIL_COUNT+1))
        echo "✗ Task 3 failed (see details in $LOG)"
    fi
else
    echo "! Skipping full coverage because targeted tests failed (FAIL_COUNT=$FAIL_COUNT)"
fi

# 4) Parse coverage xml for line-rate (with fallback)
COV_RATE="N/A"
if [ -f "$OUTDIR/coverage.xml" ]; then
    COV_RATE=$(python3 -c "import xml.etree.ElementTree as ET; r=ET.parse('$OUTDIR/coverage.xml').getroot(); print(f\"{float(r.get('line-rate', 0)) * 100:.1f}%\")" 2>/dev/null || echo "N/A")
fi

# 5) Write summary into Obsidian daily note
mkdir -p "$OBSIDIAN_DIR"
DAILY_NOTE="$OBSIDIAN_DIR/DAILY_PROGRESS_$TS.md"
cat > "$DAILY_NOTE" <<MD
# Hermes Daily Progress - $TS

**Status**: $PASS_COUNT/$TASK_COUNT tasks passed

- timestamp: $TS
- coverage_line_rate: $COV_RATE
- output_directory: $OUTDIR
- full_log: $LOG
- task_results:
  - Task 1 (multiagent): $([ $PASS_COUNT -ge 1 ] && echo '✓ PASS' || echo '✗ FAIL')
  - Task 2 (memory): $([ $PASS_COUNT -ge 2 ] && echo '✓ PASS' || echo '✗ FAIL')
  - Task 3 (full-coverage): $([ $PASS_COUNT -ge 3 ] && echo '✓ PASS' || echo '✗ FAIL')

MD

echo "Wrote daily note: $DAILY_NOTE"

# 6) Append to running SUMMARY.md in Obsidian
SUMMARY="$OBSIDIAN_DIR/DAILY_SUMMARY.md"
if [ ! -f "$SUMMARY" ]; then
  echo "# Hermes Daily Summary" > "$SUMMARY"
fi
echo "- $TS: $PASS_COUNT/$TASK_COUNT passed | coverage=$COV_RATE | [details]($DAILY_NOTE)" >> "$SUMMARY"

echo "=== Run complete: $PASS_COUNT/$TASK_COUNT tasks passed ==="
