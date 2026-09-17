#!/usr/bin/env python3
"""生成模块骨架脚本：生成 implementation/modules/module_{NNN}.py 加测试与文档占位文件。"""
import os
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODULE_DIR = os.path.join(REPO_ROOT, 'implementation', 'modules')
TEST_DIR = os.path.join(REPO_ROOT, 'agent', 'tests')

os.makedirs(MODULE_DIR, exist_ok=True)
# create __init__.py
with open(os.path.join(MODULE_DIR, '__init__.py'), 'a') as f:
    pass

def create_module(n):
    name = f'module_{n:03d}'
    py = os.path.join(MODULE_DIR, f'{name}.py')
    md = os.path.join(MODULE_DIR, f'{name}.md')
    test = os.path.join(MODULE_DIR, f'test_{name}.py')
    if os.path.exists(py):
        return False
    with open(py, 'w') as f:
        f.write(f'"""{name} - scaffold generated at {datetime.utcnow().isoformat()}Z"""\n\n')
        f.write('def placeholder():\n')
        f.write('    """Placeholder function for module implementation."""\n')
        f.write('    return True\n')
    with open(md, 'w') as f:
        f.write(f'# {name}\n\nGenerated scaffold. Fill implementation details.\n')
    with open(test, 'w') as f:
        f.write('import pytest\n\n')
        f.write(f'from implementation.modules import {name}\n\n')
        f.write(f'def test_{name}_placeholder():\n')
        f.write('    assert {0}.placeholder() is True\n'.format(name))
    return True

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--start', type=int, default=1)
    p.add_argument('--count', type=int, default=10)
    args = p.parse_args()
    created = 0
    for i in range(args.start, args.start + args.count):
        ok = create_module(i)
        if ok:
            created += 1
            print(f'Created module_{i:03d}')
        else:
            print(f'module_{i:03d} already exists')
    print(f'Total created: {created}')
