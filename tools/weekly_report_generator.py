#!/usr/bin/env python3
"""
Generate weekly progress report and write to Obsidian Hermes inbox.
"""
from datetime import datetime
from pathlib import Path
import json
import subprocess

ROOT = Path('/Users/huchufan/Hermes')
OUT = Path('/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes')
now = datetime.now().strftime('%Y-%m-%d')

# Basic summary: recent commits to repo main, recent PR merges, test coverage

def recent_commits(n=20):
    out = subprocess.check_output(['git','-C',str(ROOT),'log','-n',str(n),'--pretty=format:%h %cs %s']).decode()
    return out

report = []
report.append(f'周报 — 自动化生成: {now}')
report.append('\n一、本周关键事件')
report.append(recent_commits(10))

# coverage
cov_xml = ROOT / 'implementation' / 'automation' / 'coverage_post_merge' / 'coverage.xml'
line_rate = None
if cov_xml.exists():
    import xml.etree.ElementTree as ET
    root = ET.parse(cov_xml).getroot()
    line_rate = float(root.attrib.get('line-rate', '0'))
    report.append('\n覆盖率 (line-rate): {:.2%}'.format(line_rate))

# Write
OUT.mkdir(parents=True, exist_ok=True)
path = OUT / f'WEEKLY_AUTOGEN_{now}.md'
with open(path,'w',encoding='utf-8') as f:
    f.write('\n\n'.join(report))
print('WROTE', path)
