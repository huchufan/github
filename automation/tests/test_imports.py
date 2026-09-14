import importlib


def test_import_automation_modules():
    mods = [
        "automation.core.executor",
        "automation.core.healing",
        "automation.core.loadbalance",
        "automation.core.scheduler",
        "automation.core.triggers",
    ]
    for m in mods:
        mod = importlib.import_module(m)
        assert getattr(mod, "__name__", None) == m
