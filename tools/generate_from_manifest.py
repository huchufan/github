#!/usr/bin/env python3
import json, os, subprocess
from pathlib import Path

ROOT = Path('/Users/huchufan/Hermes')
MANIFEST = ROOT / 'tools' / 'MODULE_MANIFEST.json'
GEN = ROOT / 'tools' / 'generators' / 'module_generator.py'
TARGET = 114

def load_manifest():
    with open(MANIFEST,'r',encoding='utf-8') as f:
        return json.load(f)

def save_manifest(m):
    with open(MANIFEST,'w',encoding='utf-8') as f:
        json.dump(m,f,ensure_ascii=False,indent=2)

def main():
    m = load_manifest()
    current = m.get('total_modules',0)
    need = TARGET - current
    if need <= 0:
        print('No modules needed; current', current)
        return
    frameworks = list(m['frameworks'].keys())
    i = 1
    fw_i = 0
    added = {fw:[] for fw in frameworks}
    while need>0:
        fw = frameworks[fw_i % len(frameworks)]
        name = f"{fw}_extra_{i:03d}"
        # avoid duplicates
        if name in m['frameworks'][fw]['modules']:
            i += 1
            fw_i += 1
            continue
        # call generator
        print('Generating', fw, name)
        res = subprocess.run([str(GEN), fw, name], cwd=str(ROOT))
        if res.returncode != 0:
            raise SystemExit('generator failed for %s %s' % (fw,name))
        m['frameworks'][fw]['modules'].append(name)
        added[fw].append(name)
        i += 1
        fw_i += 1
        need -= 1
    m['total_modules'] = TARGET
    save_manifest(m)
    print('Done. Added counts:', {fw: len(v) for fw,v in added.items()})

if __name__=='__main__':
    main()
