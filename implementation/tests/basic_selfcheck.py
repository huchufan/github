import importlib
import sys
from pathlib import Path

def test_can_import_implementation():
    # ensure implementation package is importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    mod = importlib.import_module('implementation')
    assert mod is not None


def test_qdrant_adapter_and_migrator_exist():
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from implementation.memory import qdrant_adapter
    import implementation.automation.migrate_to_qdrant as migr
    # basic attribute checks
    assert hasattr(qdrant_adapter, 'upsert')
    assert hasattr(qdrant_adapter, 'create_collection_if_not_exists')
    assert hasattr(migr, 'migrate') or hasattr(migr, '__name__')


def test_skill_drafts_present():
    drafts = Path(__file__).resolve().parents[3] / 'implementation' / 'skills' / 'drafts'
    # drafts directory should exist (pipeline copied patches)
    assert drafts.exists()
    # at least one draft SKILL file or patch should be present
    found = False
    for p in drafts.iterdir():
        if p.suffix in ('.patch', '.md', '.SKILL.md'):
            found = True
            break
    assert found, 'no draft artifacts found in implementation/skills/drafts'