#!/bin/bash
set -e
REPO_DIR="/Users/huchufan/Hermes"
cd "$REPO_DIR"

create_issue(){
  title="$1"
  body="$2"
  # create issue with label implementation; ignore failures for unknown users
  gh issue create --title "$title" --body "$body" --label implementation || true
}

# Lists: first 10 extras per framework as in manifest
declare -A lists
lists[governance]="governance_extra_001 governance_extra_007 governance_extra_013 governance_extra_019 governance_extra_025 governance_extra_031 governance_extra_037 governance_extra_043 governance_extra_049 governance_extra_055"
lists[orchestration]="orchestration_extra_002 orchestration_extra_008 orchestration_extra_014 orchestration_extra_020 orchestration_extra_026 orchestration_extra_032 orchestration_extra_038 orchestration_extra_044 orchestration_extra_050 orchestration_extra_056"
lists[memory]="memory_extra_003 memory_extra_009 memory_extra_015 memory_extra_021 memory_extra_027 memory_extra_033 memory_extra_039 memory_extra_045 memory_extra_051 memory_extra_057"
lists[automation]="automation_extra_004 automation_extra_010 automation_extra_016 automation_extra_022 automation_extra_028 automation_extra_034 automation_extra_040 automation_extra_046 automation_extra_052 automation_extra_058"
lists[evolution]="evolution_extra_005 evolution_extra_011 evolution_extra_017 evolution_extra_023 evolution_extra_029 evolution_extra_035 evolution_extra_041 evolution_extra_047 evolution_extra_053 evolution_extra_059"
lists[multiagent]="multiagent_extra_006 multiagent_extra_012 multiagent_extra_018 multiagent_extra_024 multiagent_extra_030 multiagent_extra_036 multiagent_extra_042 multiagent_extra_048 multiagent_extra_054 multiagent_extra_060"

for fw in "governance orchestration memory automation evolution multiagent"; do
  owner="@${fw}-lead"
  for m in ${lists[$fw]}; do
    title="Implement module: $m"
    body="Scaffold: agent/$fw/core/$m.py\nTypes: agent/$fw/core/${m}_types.py\nTest: agent/$fw/tests/test_${m}.py\nSuggested owner: $owner\nAcceptance: implement execute() logic, add unit tests, open PR referencing this issue."
    echo "Creating issue: $title"
    create_issue "$title" "$body"
  done
done

echo "DONE_ISSUE_CREATION"
