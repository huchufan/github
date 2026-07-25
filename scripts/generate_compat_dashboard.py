#!/usr/bin/env python3
"""
Generate compatibility weekly dashboard from weekly_rollups state files and
write a human-friendly mermaid markdown into INBOX. Produces a small trend and
summary that highlights package_compat_risk occurrences.
"""
import os, json, glob
from datetime import datetime
HOME = os.path.expanduser('~')
HERMES_HOME = os.environ.get('HERMES_HOME', os.path.join(HOME, 'Hermes/.hermes'))
STATE_DIR = os.path.join(HERMES_HOME, 'state', 'weekly_rollups')
INBOX = os.path.join(HOME, 'Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes')
os.makedirs(INBOX, exist_ok=True)

files = sorted(glob.glob(os.path.join(STATE_DIR, '*_weekly_rollup.json')))
# pick last 8 (8 weeks)
files = files[-8:]
weeks = []
ok_count = 0
high_count = 0
for p in files:
    try:
        j = json.load(open(p))
        ts = j.get('ts','')
        metric = j.get('metrics', {}).get('package_compat_risk', 'UNKNOWN')
        weeks.append((ts, metric))
        if metric == 'LOW' or metric == 'OK' or metric == 'Ok':
            ok_count += 1
        elif metric == 'HIGH':
            high_count += 1
    except Exception:
        weeks.append((os.path.basename(p), 'ERR'))

now = datetime.now().strftime('%Y%m%dT%H%M%S')
md_path = os.path.join(INBOX, f'{now}_compatibility_weekly_dashboard.md')
with open(md_path, 'w') as f:
    f.write('---\n')
    f.write('title: Compatibility Weekly Dashboard\n')
    f.write(f'date: {datetime.now().isoformat()}\n')
    f.write('tags: [compatibility,weekly,dashboard]\n')
    f.write('---\n\n')
    f.write('## Summary\n\n')
    f.write(f'- Weeks considered: {len(weeks)}\n')
    f.write(f'- LOW/OK weeks: {ok_count}\n')
    f.write(f'- HIGH weeks: {high_count}\n\n')
    f.write('### Trend (last weeks)\n\n')
    # simple bar-like mermaid gantt or sequence; use pie or bar
    # We'll use a simple textual representation and a mermaid pie for counts
    f.write('```mermaid\n')
    f.write('pie title Compatibility Risk (recent weeks)\n')
    f.write(f'  "LOW/OK" : {ok_count}\n')
    f.write(f'  "HIGH" : {high_count}\n')
    f.write('```\n\n')
    f.write('### Week details\n\n')
    for ts, m in weeks:
        f.write(f'- {ts}: {m}\n')

print(md_path)
