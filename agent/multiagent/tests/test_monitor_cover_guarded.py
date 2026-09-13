import asyncio
from agent.multiagent.tests.test_monitor_cover import DummyAgent


def test_cluster_monitor_collect_and_detect_sync():
    from agent.multiagent.core.monitor import ClusterMonitor

    class Life:
        def get_all_agents(self):
            return [DummyAgent('a1'), DummyAgent('a2', state='FAILED', cpu=95, memory=95, resp=10000, failed=5)]

    cm = ClusterMonitor(lifecycle=Life())
    metrics = cm.collect_cluster_metrics()
    # If collect_cluster_metrics returned a coroutine, run it
    if asyncio.iscoroutine(metrics):
        metrics = asyncio.run(metrics)

    assert metrics.total_agents == 2
    anomalies = cm.detect_anomalies(metrics)
    assert any(a.type == 'HIGH_FAILURE_RATE' for a in anomalies)
    assert any(a.type == 'SLOW_RESPONSE' for a in anomalies)
