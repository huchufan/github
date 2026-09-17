#!/bin/bash
set -euo pipefail
ROOT="/Users/huchufan/Hermes"
cd "$ROOT"
modules=(automation_extra_004 automation_extra_010 automation_extra_016 automation_extra_022 automation_extra_028 automation_extra_034 automation_extra_040 automation_extra_046 automation_extra_052 automation_extra_058 automation_extra_064 automation_extra_070 automation_extra_076)
for m in "${modules[@]}"; do
  branch="feat/impl/$m"
  rm -f "$HOME/.git/index.lock" || true
  git checkout -B "$branch" || true
  mkdir -p implementation/impl_starts
  cat > implementation/impl_starts/PR_DRAFT_${m}.md <<MD
Title: impl(${m}): start implementation

Description:
- Module: agent/automation/core/${m}.py
- Tasks: implement triggers/scheduler hooks, add unit tests in agent/automation/tests/test_${m}.py

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

echo "DONE_BATCH_CREATE_AUTOMATION"
