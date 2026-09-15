from pathlib import Path

import yaml

REGISTRY_PATH = Path(__file__).parent / "registry.yaml"


def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    agents = {}
    for entry in data.get("agents", []):
        agent_id = entry["id"]
        agents[agent_id] = entry
    return agents


if __name__ == "__main__":
    print(load_registry())
