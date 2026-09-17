#!/bin/bash
set -euo pipefail
ROOT="/Users/huchufan/Hermes"
cd "$ROOT"
modules=(evolution_extra_005 evolution_extra_011 evolution_extra_017 evolution_extra_023 evolution_extra_029 evolution_extra_035 evolution_extra_041 evolution_extra_047 evolution_extra_053 evolution_extra_059 evolution_extra_065 evolution_extra_071 evolution_extra_077)
for m in "${modules[@]}"; do
  branch="feat/impl/$m"
  rm -f "$HOME/.git/index.lock" || true
  git checkout -B "$branch" || true
  mkdir -p implementation/impl_starts
  cat > implementation/impl_starts/PR_DRAFT_${m}.md <<MD
Title: impl(${m}): start implementation

Description:
- Module: agent/evolution/core/${m}.py
- Tasks: implement learning loop, add unit tests in agent/evolution/tests/test_${m}.py

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

echo "DONE_BATCH_CREATE_EVOLUTION"
