# Pytest conftest to install a noop prometheus_client shim for tests
import sys
import types
from types import SimpleNamespace

# If prometheus_client is already loaded, replace it with a noop shim to prevent
# CollectorRegistry duplicate timeseries errors when tests import modules that
# register metrics at import or construct time.
if "prometheus_client" not in sys.modules:
    fake = types.ModuleType("prometheus_client")

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
    fake.generate_latest = lambda *a, **k: b""
    fake.start_http_server = lambda *a, **k: None
    sys.modules["prometheus_client"] = fake
else:
    # Replace existing with noop shim
    fake = types.ModuleType("prometheus_client")

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
    fake.generate_latest = lambda *a, **k: b""
    fake.start_http_server = lambda *a, **k: None
    sys.modules["prometheus_client"] = fake
