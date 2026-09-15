import pytest

from agent.multiagent.health_monitor import HealthMonitor


def test_health_monitor_run_once():
    m = HealthMonitor(interval=1.0, start_http=False)
    res = m.run_once_blocking()
    assert isinstance(res, dict)
    # expecting T1 at least present
    assert "T1" in res
