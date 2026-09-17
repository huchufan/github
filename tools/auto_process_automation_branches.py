#!/usr/bin/env python3
import subprocess, json, os, xml.etree.ElementTree as ET
ROOT='/Users/huchufan/Hermes'
os.chdir(ROOT)
# list remote branches matching pattern (full remote ref)
p = subprocess.run(['git','-C',ROOT,'branch','-r','--list','origin/feat/impl/automation_*'], capture_output=True, text=True)
branches = [b.strip() for b in p.stdout.splitlines() if b.strip()]
report=[]
for branch_full in branches:
    # branch_full example: origin/feat/impl/automation_extra_004
    branch_local = branch_full.replace('origin/','')
    entry={'branch':branch_local}
    print('Processing',branch_local)
    # fetch and checkout local branch
    subprocess.run(['git','fetch','origin',branch_local], check=False)
    subprocess.run(['git','checkout','-B',branch_local, branch_full], check=False)
    module = branch_local.split('/')[-1]
    testpath=os.path.join(ROOT,'agent','automation','tests',f'test_{module}.py')
    entry['testpath']=testpath
    if not os.path.exists(testpath):
        entry['pytest_rc']=None
        entry['note']='test missing'
        report.append(entry)
        print(' - test missing')
        continue
    # run pytest
    r = subprocess.run(['python3','-m','pytest','-q',testpath], capture_output=True, text=True)
    entry['pytest_rc']=r.returncode
    entry['pytest_out_tail']=r.stdout.strip().splitlines()[-5:] if r.stdout else []
    if r.returncode!=0:
        entry['merge']=False; entry['reason']='pytest failed'
        report.append(entry); print(' - pytest failed'); continue
    # run coverage
    subprocess.run(['python3','-m','coverage','run','-m','pytest','-q'], check=False)
    subprocess.run(['python3','-m','coverage','xml','-o','implementation/automation/coverage_tmp.xml'], check=False)
    try:
        tree=ET.parse('implementation/automation/coverage_tmp.xml')
        lr=float(tree.getroot().attrib.get('line-rate','0'))
    except Exception:
        lr=0.0
    entry['coverage_line_rate']=lr
    if lr>=0.85:
        # create PR if none
        pjson = subprocess.run(['gh','pr','list','--state','open','--json','number,headRefName','-L','200'], capture_output=True, text=True)
        opens = []
        try:
            opens = json.loads(pjson.stdout)
        except:
            opens=[]
        existing = [o for o in opens if o.get('headRefName','')==branch_local]
        prnum=None
        if not existing:
            title=f"impl(automation): {branch_local} implementation"
            body=f"Auto-generated PR for {branch_local} — implement module and tests."
            cr = subprocess.run(['gh','pr','create','--title',title,'--body',body,'--head',branch_local,'--base','main','--assignee','@me'], capture_output=True, text=True)
            pjson = subprocess.run(['gh','pr','list','--state','open','--json','number,headRefName','-L','200'], capture_output=True, text=True)
            try:
                opens = json.loads(pjson.stdout)
                existing = [o for o in opens if o.get('headRefName','')==branch_local]
            except:
                existing=[]
        if existing:
            prnum=existing[0].get('number')
        entry['pr']=prnum
        if prnum is not None:
            m = subprocess.run(['gh','pr','merge',str(prnum),'--merge','--admin'], capture_output=True, text=True)
            entry['merge_rc']=m.returncode
            entry['merge_out']=(m.stdout+'\n'+m.stderr).strip()
            entry['merge']=(m.returncode==0)
        else:
            entry['merge']=False; entry['reason']='pr create/list failed'
    else:
        entry['merge']=False; entry['reason']='coverage below threshold'
    report.append(entry)
# write outputs
out_json=os.path.join(ROOT,'implementation','impl_starts','AUTOMATION_IMPL_PROGRESS.json')
with open(out_json,'w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
md_lines=['# Automation PR Auto-Process Report']
for e in report:
    md_lines.append(f"- branch={e.get('branch')}, pr={e.get('pr')}, pytest_rc={e.get('pytest_rc')}, coverage={e.get('coverage_line_rate')}, merged={e.get('merge')}, note={e.get('reason',e.get('note',''))}")
summary_dir='/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes'
os.makedirs(summary_dir, exist_ok=True)
md_path=os.path.join(summary_dir,'AUTOMATION_IMPL_PROGRESS.md')
with open(md_path,'w',encoding='utf-8') as f:
    f.write('\n'.join(md_lines))
print('WROTE',out_json,md_path)
print(json.dumps(report,ensure_ascii=False,indent=2))
