import pytest
import asyncio

from agent.multiagent.core.monitor import ClusterMonitor, ClusterOptimizer
from agent.core.types import ClusterMetrics, Severity, Anomaly, OptimizationOpportunity


class DummyAgent:
    def __init__(self, id, state='RUNNING', cpu=10, memory=20, load=0.1, resp=100, tasks=0, completed=0, failed=0):
        self.id = id
        self.state = state
        self.cpu_usage = cpu
        self.memory_usage = memory
        self.current_load = load
        self.avg_response_time = resp
        self.task_count = tasks
        self.completed_tasks = completed
        self.failed_tasks = failed


def test_cluster_monitor_collect_and_detect():
    class Life:
        async def get_all_agents(self):
            return [DummyAgent('a1'), DummyAgent('a2', state='FAILED', cpu=95, memory=95, resp=10000, failed=5)]

    cm = ClusterMonitor(lifecycle=Life())
    metrics = asyncio.run(cm.collect_cluster_metrics())
    assert metrics.total_agents == 2
    anomalies = cm.detect_anomalies(metrics)
    assert any(a.type == 'HIGH_FAILURE_RATE' for a in anomalies)
    assert any(a.type == 'SLOW_RESPONSE' for a in anomalies)


def test_optimizer_identify_and_optimize():
    co = ClusterOptimizer()
    history = [{'load': 0.1}, {'load': 1.0}, {'load': 0.2}]
    opps = co.identify_optimization_opportunities(history)
    assert len(opps) >= 1
    applied = asyncio.run(co.optimize_cluster_configuration(history))
    assert applied == opps
