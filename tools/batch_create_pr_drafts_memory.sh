#!/bin/bash
set -euo pipefail
ROOT="/Users/huchufan/Hermes"
cd "$ROOT"
modules=(memory_extra_003 memory_extra_009 memory_extra_015 memory_extra_021 memory_extra_027 memory_extra_033 memory_extra_039 memory_extra_045 memory_extra_051 memory_extra_057 memory_extra_063 memory_extra_069 memory_extra_075 memory_extra_081)
for m in "${modules[@]}"; do
  branch="feat/impl/$m"
  rm -f "$HOME/.git/index.lock" || true
  git checkout -B "$branch" || true
  mkdir -p implementation/impl_starts
  cat > implementation/impl_starts/PR_DRAFT_${m}.md <<MD
Title: impl(${m}): start implementation

Description:
- Module: agent/memory/core/${m}.py
- Tasks: implement storage/retrieval, add unit tests in agent/memory/tests/test_${m}.py

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

echo "DONE_BATCH_CREATE_MEMORY"
