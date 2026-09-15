import importlib


def test_import_evolution_type_modules():
    mods = [
        "agent.evolution.core.analyzer_types",
        "agent.evolution.core.distiller_types",
        "agent.evolution.core.learner_types",
        "agent.evolution.core.optimizer_types",
    ]
    for m in mods:
        mod = importlib.import_module(m)
        assert getattr(mod, "__name__", None) == m
