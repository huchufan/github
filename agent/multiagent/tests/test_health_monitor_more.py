import sys
import types
import time
from types import SimpleNamespace

import pytest

# Ensure prometheus_client shim exists before importing health_monitor module
fake = types.ModuleType('prometheus_client')
class NoopMetric:
    def __init__(self, *a, **k):
        pass
    def labels(self, *a, **k):
        return self
    def set(self, *a, **k):
        return None
    def observe(self, *a, **k):
        return None
fake.Gauge = NoopMetric
fake.Histogram = NoopMetric
fake.CollectorRegistry = lambda *a, **k: None
fake.REGISTRY = SimpleNamespace()
fake.generate_latest = lambda *a, **k: b''
fake.start_http_server = lambda *a, **k: None
sys.modules['prometheus_client'] = fake

from agent.multiagent.health_monitor import HealthMonitor
import agent.multiagent.router as router


def test_run_once_blocking_uses_router(monkeypatch):
    # monkeypatch router.run_health_check_once to return a controlled summary
    def fake_run():
        return {"T1": {"availability": 1, "latency_ms": 12, "confidence": 0.82, "status": "ok"}}

    monkeypatch.setattr(router, "run_health_check_once", fake_run)

    m = HealthMonitor(interval=0.1, start_http=False)
    res = m.run_once_blocking()
    assert isinstance(res, dict)
    assert "T1" in res
    assert res["T1"]["availability"] == 1


def test_update_metrics_noop_and_custom_metric_object():
    # create monitor but avoid global prometheus registry duplication by forcing no-op metrics
    m = HealthMonitor(interval=0.1, start_http=False)

    class DummyMetric:
        def labels(self, **kwargs):
            return self

        def set(self, v):
            # record a simple attribute
            self.last = v

        def observe(self, v):
            self.obs = getattr(self, 'obs', 0) + float(v)

    # replace metrics with dummy objects to avoid interacting with CollectorRegistry
    m.availability_gauge = DummyMetric()
    m.latency_hist = DummyMetric()
    m.last_check_gauge = DummyMetric()

    summary = {
        "T1": {"availability": 1, "latency_ms": 5, "confidence": 0.9},
        "T2": {"availability": 0, "latency_ms": None, "confidence": None},
    }

    # should not raise
    m._update_metrics(summary)

    # confirm dummy metric recorded something for T1 last_check
    assert hasattr(m.last_check_gauge, 'last') or hasattr(m.availability_gauge, 'last')


def test_start_and_stop_thread_lifecycle():
    # ensure metrics are noop to avoid registry duplicates when starting thread
    m = HealthMonitor(interval=0.05, start_http=False)
    m.availability_gauge = lambda *a, **k: None
    m.latency_hist = lambda *a, **k: None
    m.last_check_gauge = lambda *a, **k: None

    m.start()
    # let it run a short while
    time.sleep(0.12)
    # stop should join thread and clear it
    m.stop(timeout=1.0)
    assert m._thread is None
