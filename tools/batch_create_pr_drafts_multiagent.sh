#!/bin/bash
set -euo pipefail
ROOT="/Users/huchufan/Hermes"
cd "$ROOT"
modules=(multiagent_extra_006 multiagent_extra_012 multiagent_extra_018 multiagent_extra_024 multiagent_extra_030 multiagent_extra_036 multiagent_extra_042 multiagent_extra_048 multiagent_extra_054 multiagent_extra_060 multiagent_extra_066 multiagent_extra_072 multiagent_extra_078)
for m in "${modules[@]}"; do
  branch="feat/impl/$m"
  rm -f "$HOME/.git/index.lock" || true
  git checkout -B "$branch" || true
  mkdir -p implementation/impl_starts
  cat > implementation/impl_starts/PR_DRAFT_${m}.md <<MD
Title: impl(${m}): start implementation

Description:
- Module: agent/multiagent/core/${m}.py
- Tasks: implement lifecycle/coordination hooks, add unit tests in agent/multiagent/tests/test_${m}.py

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

echo "DONE_BATCH_CREATE_MULTIAGENT"
