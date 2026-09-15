import yaml
from pathlib import Path
from typing import Optional


def _read_file_text(path: Optional[str]):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding='utf-8')
    except Exception:
        return None


def get_agent(agent_id: str, enrich: bool = True):
    """Return agent registry entry.

    If enrich=True, read profile.yaml, soul.md, SKILL.md and list workspace files.
    """
    # Import AGENT_REGISTRY lazily to avoid circular import at module import time
    from agent.multiagent import AGENT_REGISTRY

    entry = AGENT_REGISTRY.get(agent_id)
    if not entry or not enrich:
        return entry

    result = dict(entry)  # shallow copy

    # Read profile.yaml if present
    profile_path = entry.get('profile_path')
    if profile_path:
        try:
            ptext = _read_file_text(profile_path)
            if ptext:
                result['profile'] = yaml.safe_load(ptext)
            else:
                result['profile'] = None
        except Exception:
            result['profile'] = None

    # Read soul (text)
    soul_path = entry.get('soul')
    result['soul'] = _read_file_text(soul_path)

    # Read SKILL.md text
    skill_path = entry.get('skill')
    result['skill_text'] = _read_file_text(skill_path)

    # List workspace files (top-level)
    workspace = entry.get('workspace')
    if workspace:
        ws = Path(workspace)
        if ws.is_dir():
            try:
                result['workspace_files'] = [str(p.name) for p in sorted(ws.iterdir())]
            except Exception:
                result['workspace_files'] = None
        else:
            result['workspace_files'] = None
    else:
        result['workspace_files'] = None

    return result
