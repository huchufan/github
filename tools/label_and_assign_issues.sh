#!/bin/bash
set -e
REPO="huchufan/github"
# mapping
declare -A MAP
MAP[governance]=gov-lead
MAP[orchestration]=orch-lead
MAP[memory]=memory-lead
MAP[automation]=automation-lead
MAP[evolution]=evolution-lead
MAP[multiagent]=multiagent-lead

OUT_LOG="/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes/automation/issue_label_assign_log_$(date +%Y%m%d_%H%M%S).md"
echo "# Issue label/assign run" > "$OUT_LOG"

echo "Fetching open issues..." | tee -a "$OUT_LOG"
issues_json=$(gh issue list --repo $REPO --state open --limit 200 --json number,title,labels)

if [ -z "$issues_json" ] || [ "$issues_json" = "[]" ]; then
  echo "No open issues found." | tee -a "$OUT_LOG"
  exit 0
fi

echo "$issues_json" | jq -c '.[]' | while read -r issue; do
  num=$(echo "$issue" | jq -r '.number')
  title=$(echo "$issue" | jq -r '.title')
  labels=$(echo "$issue" | jq -r '[.labels[].name] | join(", ")')
  echo "Processing #$num - $title" | tee -a "$OUT_LOG"

  # add label implementation
  if gh issue edit "$num" --repo $REPO --add-label implementation >/dev/null 2>&1; then
    echo " - Added label 'implementation'" | tee -a "$OUT_LOG"
  else
    echo " - Failed to add label (will continue)" | tee -a "$OUT_LOG"
  fi

  # parse module name from title, expecting format 'Implement module: <module>'
  module=$(echo "$title" | sed -n 's/^Implement module: \(.*\)/\1/p')
  if [ -z "$module" ]; then
    echo " - Not a scaffold issue (skipping assignee)" | tee -a "$OUT_LOG"
    continue
  fi

  # determine framework by prefix
  framework=""
  for fw in governance orchestration memory automation evolution multiagent; do
    if [[ "$module" == ${fw}_* ]]; then
      framework=$fw
      break
    fi
  done
  if [ -z "$framework" ]; then
    echo " - Could not determine framework for module $module" | tee -a "$OUT_LOG"
    continue
  fi

  assignee="${MAP[$framework]}"
  if [ -z "$assignee" ]; then
    echo " - No assignee mapping for $framework" | tee -a "$OUT_LOG"
    continue
  fi

  # try to add assignee
  if gh issue edit "$num" --repo $REPO --add-assignee "$assignee" >/dev/null 2>&1; then
    echo " - Assigned to $assignee" | tee -a "$OUT_LOG"
  else
    echo " - Could not assign $assignee (fallback: add comment)" | tee -a "$OUT_LOG"
    gh issue comment "$num" --repo $REPO --body "@${assignee} not found or cannot be assigned automatically. Please assign this issue to ${assignee}." >/dev/null 2>&1 || true
  fi

done

echo "Run complete." | tee -a "$OUT_LOG"
cat "$OUT_LOG"
