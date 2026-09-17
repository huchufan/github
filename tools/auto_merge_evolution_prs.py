#!/usr/bin/env python3
import subprocess, json, os, xml.etree.ElementTree as ET
ROOT = '/Users/huchufan/Hermes'
os.chdir(ROOT)

def gh_pr_list():
    p = subprocess.run(['gh','pr','list','--state','open','--json','number,headRefName,title','-L','200'], capture_output=True, text=True)
    if p.returncode != 0:
        return []
    try:
        return json.loads(p.stdout)
    except Exception:
        return []

prs = gh_pr_list()
report = []
for pr in prs:
    head = pr.get('headRefName') or ''
    if not head.startswith('feat/impl/evolution_'):
        continue
    num = pr.get('number')
    module = head.split('/')[-1]
    entry = {'pr': num, 'branch': head, 'module': module}
    testpath = os.path.join(ROOT, 'agent', 'evolution', 'tests', f'test_{module}.py')
    if not os.path.exists(testpath):
        entry['pytest_rc'] = None
        entry['note'] = 'test missing'
        report.append(entry)
        continue
    p = subprocess.run(['python3','-m','pytest','-q', testpath], capture_output=True, text=True)
    entry['pytest_rc'] = p.returncode
    entry['pytest_out_tail'] = p.stdout.strip().splitlines()[-5:]
    if p.returncode != 0:
        entry['merge'] = False
        entry['reason'] = 'pytest failed'
        report.append(entry)
        continue
    subprocess.run(['python3','-m','coverage','run','-m','pytest','-q'], check=False)
    subprocess.run(['python3','-m','coverage','xml','-o','implementation/automation/coverage_tmp.xml'], check=False)
    lr = 0.0
    try:
        tree = ET.parse('implementation/automation/coverage_tmp.xml')
        lr = float(tree.getroot().attrib.get('line-rate','0'))
    except Exception:
        lr = 0.0
    entry['coverage_line_rate'] = lr
    if lr >= 0.85:
        m = subprocess.run(['gh','pr','merge', str(num), '--merge', '--admin'], capture_output=True, text=True)
        entry['merge_rc'] = m.returncode
        entry['merge_out'] = (m.stdout + '\n' + m.stderr).strip()
        entry['merge'] = (m.returncode == 0)
    else:
        entry['merge'] = False
        entry['reason'] = 'coverage below threshold'
    report.append(entry)

out_json = os.path.join(ROOT, 'implementation', 'impl_starts', 'EVOLUTION_IMPL_PROGRESS.json')
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

lines = ['# Evolution PR Auto-Merge Report']
for e in report:
    lines.append(f"- PR #{e.get('pr')} ({e.get('branch')}): module={e.get('module')}, pytest_rc={e.get('pytest_rc')}, coverage={e.get('coverage_line_rate')}, merged={e.get('merge')}")
summary_path = '/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes/EVOLUTION_IMPL_PROGRESS.md'
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('WROTE', out_json, summary_path)
print(json.dumps(report, ensure_ascii=False, indent=2))
