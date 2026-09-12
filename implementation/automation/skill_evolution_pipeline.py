"""Skill evolution pipeline (PoC)

- Collect patches from implementation/skills/patches/
- Create draft SKILL updates under implementation/skills/drafts/
- Run unit tests (pytest) to validate changes
- Produce a validation report into Obsidian and a TODO checklist for remaining items
"""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PATCH_DIR = ROOT / 'implementation' / 'skills' / 'patches'
DRAFT_DIR = ROOT / 'implementation' / 'skills' / 'drafts'
REPORT = ROOT / 'implementation' / 'automation' / 'skill_evolution_report.md'

DRAFT_DIR.mkdir(parents=True, exist_ok=True)

applied = []
errors = []

for p in sorted(PATCH_DIR.glob('*.patch')):
    try:
        # Simulate applying: copy patch to drafts with .patch and create a placeholder SKILL.md
        target_patch = DRAFT_DIR / p.name
        shutil.copy(p, target_patch)
        skill_name = p.stem
        skill_md = DRAFT_DIR / (skill_name + '.SKILL.md')
        skill_md.write_text(f"# Draft applied from {p.name}\n\n(Review required)\n")
        applied.append(p.name)
    except Exception as e:
        errors.append((p.name, str(e)))

# Run pytest (limit to quick tests under agent/multiagent and implementation/tests if present)
pytest_cmd = ['python3', '-m', 'pytest', '-q', 'agent/multiagent/tests', 'implementation/tests']
try:
    proc = subprocess.run(pytest_cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    tests_out = proc.stdout + '\n' + proc.stderr
    tests_rc = proc.returncode
except Exception as e:
    tests_out = str(e)
    tests_rc = -1

report_lines = []
report_lines.append('# Skill Evolution Pipeline Report')
report_lines.append('')
report_lines.append('Applied patches (copied to drafts):')
for a in applied:
    report_lines.append(f'- {a}')
report_lines.append('')
if errors:
    report_lines.append('Errors during apply:')
    for e in errors:
        report_lines.append(f'- {e[0]}: {e[1]}')
    report_lines.append('')
report_lines.append('Pytest quick-run:')
report_lines.append(f'- return_code: {tests_rc}')
report_lines.append('```')
report_lines.append(tests_out[:20000])
report_lines.append('```')
report_lines.append('')
report_lines.append('Next actions:')
report_lines.append('- Reviewer: inspect files under implementation/skills/drafts/ and approve/merge to SKILL.md')
report_lines.append('- Add automated validation harness: run task replay + unit tests + integration tests')

REPORT.write_text('\n'.join(report_lines), encoding='utf-8')
print('done')
