import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROUTING_TABLE_PATH = Path(
    "/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes/agent_model_routing_table.yaml"
)
AUDIT_LOG = Path("/Users/huchufan/Hermes/agent/multiagent/router_audit.log")

_lock = threading.Lock()


def _load_table():
    with open(ROUTING_TABLE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _call_model_sim(
    model_key: str, timeout_ms: int, task: Dict[str, Any]
) -> Dict[str, Any]:
    """Simulated model call for smoke test. Returns metadata dict."""
    # Simulate latency and confidence by simple heuristics
    start = time.time()
    # fake latency based on model tier
    latency = timeout_ms / 1000.0 * 0.5
    time.sleep(min(latency, timeout_ms / 1000.0))
    # simulated confidence heuristic
    confidence = 0.7
    if task.get("requires_deep_reasoning"):
        confidence = 0.6 if model_key == "T3" else 0.8
    return {
        "model_key": model_key,
        "latency_ms": int((time.time() - start) * 1000),
        "confidence": confidence,
        "output": f"simulated output from {model_key}",
    }


def _audit(event: Dict[str, Any]):
    with _lock:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(yaml.safe_dump(event, allow_unicode=True))
            f.write("---\n")


def choose_model(agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    """Choose model following routing table rules. Returns chosen_model metadata and audit.

    task: {risk: LOW/MEDIUM/HIGH, cost_budget: float USD, sensitivity_level: PUBLIC/INTERNAL/CONFIDENTIAL/PII, requires_deep_reasoning: bool}
    """
    table = _load_table()
    agents = table.get("agents", {})
    defaults = table.get("defaults", {})
    timeouts = defaults.get(
        "timeouts_ms", {"T1": 3000, "T2": 8000, "T3": 1500, "T0": 2000}
    )
    confidence_threshold = defaults.get("confidence_threshold", 0.6)
    consistency_threshold = defaults.get("consistency_threshold", 0.85)

    entry = agents.get(agent_id)
    if not entry:
        raise KeyError(f"Unknown agent_id {agent_id}")

    order = [
        entry.get("preferred"),
        entry.get("upgrade"),
        entry.get("downgrade"),
        entry.get("fallback"),
    ]
    # normalize
    order = [o for o in order if o]

    audit_record = {
        "agent_id": agent_id,
        "task_meta": task,
        "attempts": [],
        "chosen": None,
        "reason": None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # HIGH risk: parallel T1+T2
    if task.get("risk") == "HIGH" and "T1" in order and "T2" in order:
        r1 = _call_model_sim("T1", timeouts.get("T1", 3000), task)
        r2 = _call_model_sim("T2", timeouts.get("T2", 8000), task)
        audit_record["attempts"].append(r1)
        audit_record["attempts"].append(r2)
        # simple consistency check: confidence close enough
        if abs(r1["confidence"] - r2["confidence"]) < 0.2:
            audit_record["chosen"] = r1
            audit_record["reason"] = "parallel_consistent"
            _audit(audit_record)
            return audit_record
        else:
            audit_record["reason"] = "parallel_inconsistent_human_review"
            _audit(audit_record)
            return audit_record

    # cost-aware: if cost budget below threshold, prefer T3
    low_cost_threshold = defaults.get("low_cost_threshold_usd", 0.01)
    if (
        task.get("cost_budget") is not None
        and task.get("cost_budget") < low_cost_threshold
        and "T3" in order
    ):
        order = ["T3"] + [o for o in order if o != "T3"]

    # sequential try chain
    for model_key in order:
        timeout = timeouts.get(model_key, 2000)
        try:
            res = _call_model_sim(model_key, timeout, task)
            audit_record["attempts"].append(res)
            if res["confidence"] >= confidence_threshold:
                audit_record["chosen"] = res
                audit_record["reason"] = "confidence_ok"
                _audit(audit_record)
                return audit_record
            # else try next
        except Exception as e:
            audit_record["attempts"].append({"model_key": model_key, "error": str(e)})
            continue

    # fallback: call T0
    res = _call_model_sim("T0", timeouts.get("T0", 2000), task)
    audit_record["attempts"].append(res)
    audit_record["chosen"] = res
    audit_record["reason"] = "fallback"
    _audit(audit_record)
    return audit_record


def run_health_check_once() -> dict:
    """Run a single-pass health check against all registered models/providers declared in routing table.

    Returns a dict mapping model_key -> {availability: 0/1, latency_ms, confidence, status}
    and writes an audit event summarizing the check.
    """
    table = _load_table()
    models = table.get("models", {})
    defaults = table.get("defaults", {})
    timeouts = defaults.get(
        "timeouts_ms", {"T1": 3000, "T2": 8000, "T3": 1500, "T0": 2000}
    )

    summary = {}
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for model_key in models.keys():
        timeout = timeouts.get(model_key, 2000)
        try:
            res = _call_model_sim(
                model_key, timeout, {"risk": "LOW", "requires_deep_reasoning": False}
            )
            availability = 1 if res and res.get("confidence") is not None else 0
            status = "ok" if availability == 1 else "degraded"
            summary[model_key] = {
                "availability": availability,
                "latency_ms": res.get("latency_ms") if res else None,
                "confidence": res.get("confidence") if res else None,
                "status": status,
            }
        except Exception as e:
            summary[model_key] = {
                "availability": 0,
                "latency_ms": None,
                "confidence": None,
                "status": "error",
                "error": str(e),
            }

    audit_event = {
        "timestamp": timestamp,
        "type": "model_health_check",
        "summary": summary,
    }
    _audit(audit_event)
    return summary


if __name__ == "__main__":
    # smoke test
    task = {
        "risk": "LOW",
        "cost_budget": 0.02,
        "requires_deep_reasoning": False,
        "sensitivity_level": "PUBLIC",
    }
    out = choose_model("code_engineer", task)
    print("SMOKE:", out)
    print("HEALTH CHECK:", run_health_check_once())
