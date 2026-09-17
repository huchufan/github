#!/bin/bash
set -euo pipefail
ROOT="/Users/huchufan/Hermes"
cd "$ROOT"
modules=(orchestration_extra_002 orchestration_extra_008 orchestration_extra_014 orchestration_extra_020 orchestration_extra_026 orchestration_extra_032 orchestration_extra_038 orchestration_extra_044 orchestration_extra_050 orchestration_extra_056)
for m in "${modules[@]}"; do
  branch="feat/impl/$m"
  rm -f "$HOME/.git/index.lock" || true
  git checkout -B "$branch" || true
  mkdir -p implementation/impl_starts
  cat > implementation/impl_starts/PR_DRAFT_${m}.md <<MD
Title: impl(${m}): start implementation

Description:
- Module: agent/orchestration/core/${m}.py
- Tasks: implement execute(), add unit tests in agent/orchestration/tests/test_${m}.py

Checklist:
- [ ] Implement module logic
- [ ] Add tests and ensure pytest passes
- [ ] Create follow-up PRs for sub-tasks

MD
  git add implementation/impl_starts/PR_DRAFT_${m}.md
  git commit -m "chore(start): draft PR for ${m}" || true
  git push origin HEAD:${branch} --set-upstream || true
  echo "CREATED ${branch} -> PR draft at implementation/impl_starts/PR_DRAFT_${m}.md"
done

echo "DONE_BATCH_CREATE_ORCH"
