#!/bin/bash
set -euo pipefail
ROOT="/Users/huchufan/Hermes"
cd "$ROOT"
modules=(governance_extra_019 governance_extra_025 governance_extra_031 governance_extra_037 governance_extra_043 governance_extra_049 governance_extra_055)
for m in "${modules[@]}"; do
  branch="feat/impl/$m"
  # remove existing lock if any
  rm -f "$HOME/.git/index.lock" || true
  # create branch
  git checkout -b "$branch" || git checkout "$branch" || true
  mkdir -p implementation/impl_starts
  cat > implementation/impl_starts/PR_DRAFT_${m}.md <<MD
Title: impl(${m}): start implementation

Description:
- Module: agent/governance/core/${m}.py
- Tasks: implement execute(), add unit tests in agent/governance/tests/test_${m}.py

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

echo "DONE_BATCH_CREATE"
