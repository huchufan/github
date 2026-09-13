#!/usr/bin/env python3
"""
Hermes module code generator (PoC)
Generates a simple module file, a types file, and a test file under agent/<framework>/core and tests.
"""
import sys
from pathlib import Path
from datetime import datetime

TEMPLATE_MODULE = '''"""
{framework_cap} Framework - {module_cap} Module
Generated: {ts}
"""

from typing import Any, Dict, Optional

class {class_name}:
    """{module_cap} module (PoC)
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {{}}

    def execute(self, *args, **kwargs) -> Any:
        """Placeholder execute"""
        return {{"module": "{module_name}", "ok": True}}

__all__ = ['{class_name}']
'''

TEMPLATE_TEST = '''"""
Auto-generated test for {module_name}
"""
import pytest
from agent.{framework}.core.{module_name} import {class_name}


def test_{module_name}_init():
    inst = {class_name}()
    assert inst.config == {{}}


def test_{module_name}_execute():
    inst = {class_name}()
    r = inst.execute()
    assert r.get('ok') is True
'''

TEMPLATE_TYPES = '''"""
Types for {module_name}
"""
from typing import Protocol, Any

class I{class_name}(Protocol):
    def execute(self, *args, **kwargs) -> Any: ...
'''


def to_camel(s: str) -> str:
    return ''.join(x.title() for x in s.split('_'))


def generate(framework: str, module: str):
    base = Path('agent') / framework / 'core'
    tests = Path('agent') / framework / 'tests'
    base.mkdir(parents=True, exist_ok=True)
    tests.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().isoformat()
    class_name = to_camel(module)

    module_path = base / f"{module}.py"
    test_path = tests / f"test_{module}.py"
    types_path = base / f"{module}_types.py"

    module_path.write_text(TEMPLATE_MODULE.format(framework_cap=framework.capitalize(), module_cap=module.capitalize(), ts=ts, class_name=class_name, module_name=module))
    test_path.write_text(TEMPLATE_TEST.format(module_name=module, framework=framework, class_name=class_name))
    types_path.write_text(TEMPLATE_TYPES.format(module_name=module, class_name=class_name))

    return module_path, test_path, types_path


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: module_generator.py <framework> <module1> [<module2> ...]')
        sys.exit(1)
    framework = sys.argv[1]
    # filter out flags like -v passed by user or CI
    modules = [m for m in sys.argv[2:] if not m.startswith('-')]
    if not modules:
        print('No modules to generate (after filtering flags).')
        sys.exit(1)
    out = []
    for m in modules:
        p = generate(framework, m)
        print('GENERATED:', p[0])
        out.append(p)
    sys.exit(0)
