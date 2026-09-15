"""Agent identity and simple mesh manager demo.
Provides register(agent_id), heartbeat(agent_id), list_agents().
"""

import json
import time
from pathlib import Path

ROOT = Path("/tmp/hermes_agent_mesh")
ROOT.mkdir(parents=True, exist_ok=True)


def register(agent_id: str, meta: dict | None = None):
    p = ROOT / f"{agent_id}.json"
    data = {"agent_id": agent_id, "meta": meta or {}, "registered_at": time.time()}
    p.write_text(json.dumps(data))
    return True


def heartbeat(agent_id: str):
    p = ROOT / f"{agent_id}.json"
    if not p.exists():
        return False
    data = json.loads(p.read_text())
    data["last_seen"] = time.time()
    p.write_text(json.dumps(data))
    return True


def list_agents():
    agents = []
    for f in ROOT.glob("*.json"):
        try:
            agents.append(json.loads(f.read_text()))
        except Exception:
            pass
    return agents
