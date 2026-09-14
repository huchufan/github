import threading
import time
from typing import Optional

try:
    from prometheus_client import (REGISTRY, CollectorRegistry, Gauge,
                                   Histogram, generate_latest,
                                   start_http_server)

    PROMETHEUS_AVAILABLE = True
except Exception:
    # prometheus_client missing: provide lightweight no-op fallbacks so tests can run
    PROMETHEUS_AVAILABLE = False

    class _NoopMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def set(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

    Gauge = Histogram = _NoopMetric

    def start_http_server(port):
        # no-op
        return None


from pathlib import Path

from agent.multiagent import router


class HealthMonitor:
    """Background monitor that periodically runs health checks and exports Prometheus metrics.

    Usage:
        m = HealthMonitor(interval=30, port=8000, start_http=False)
        m.start()
        ...
        m.stop()
    """

    def __init__(
        self, interval: float = 30.0, port: int = 8000, start_http: bool = True
    ):
        self.interval = interval
        self.port = port
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._start_http = start_http

        # Prometheus metrics (or no-op fallbacks)
        # Per-model availability gauge (0/1)
        self.availability_gauge = Gauge(
            "model_availability", "Model availability 0/1", ["model_key"]
        )
        # Per-model latency histogram
        self.latency_hist = Histogram(
            "model_latency_ms", "Model latency ms", ["model_key"]
        )
        # Last check timestamp
        self.last_check_gauge = Gauge(
            "model_last_check_timestamp", "Last health check timestamp", ["model_key"]
        )

    def _update_metrics(self, summary: dict):
        ts = int(time.time())
        for model_key, info in summary.items():
            try:
                self.availability_gauge.labels(model_key=model_key).set(
                    info.get("availability", 0) or 0
                )
                if info.get("latency_ms") is not None:
                    self.latency_hist.labels(model_key=model_key).observe(
                        float(info.get("latency_ms"))
                    )
                self.last_check_gauge.labels(model_key=model_key).set(ts)
            except Exception:
                # metric update should not crash monitor
                continue

    def _run_once(self):
        summary = router.run_health_check_once()
        self._update_metrics(summary)
        return summary

    def _loop(self):
        if self._start_http and PROMETHEUS_AVAILABLE:
            try:
                start_http_server(self.port)
            except Exception:
                # ignore http server start errors; metrics still available via REGISTRY
                pass
        while not self._stop_event.is_set():
            try:
                self._run_once()
            except Exception:
                pass
            # wait with early exit
            self._stop_event.wait(self.interval)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name="HealthMonitor", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout)
            self._thread = None

    def run_once_blocking(self):
        return self._run_once()


if __name__ == "__main__":
    m = HealthMonitor(interval=5.0, port=8000, start_http=False)
    m.start()
    try:
        time.sleep(6)
    finally:
        m.stop()
