import pytest

from agent.multiagent import AGENT_REGISTRY, router


def test_choose_model_smoke_code_engineer():
    task = {
        "risk": "LOW",
        "cost_budget": 0.02,
        "requires_deep_reasoning": False,
        "sensitivity_level": "PUBLIC",
    }
    out = router.choose_model("code_engineer", task)
    assert out["chosen"] is not None
    assert "model_key" in out["chosen"] or out["reason"] in (
        "fallback",
        "parallel_inconsistent_human_review",
    )


def test_choose_model_high_risk_parallel():
    task = {
        "risk": "HIGH",
        "cost_budget": 1.0,
        "requires_deep_reasoning": True,
        "sensitivity_level": "INTERNAL",
    }
    out = router.choose_model("agents_orchestrator", task)
    # For HIGH risk we expect a parallel decision path recorded
    assert out["reason"] in (
        "parallel_consistent",
        "parallel_inconsistent_human_review",
    )


def test_unknown_agent_raises():
    task = {"risk": "LOW"}
    with pytest.raises(KeyError):
        router.choose_model("nonexistent_agent", task)
