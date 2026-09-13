"""Simple benchmark runner for S004 performance baseline.
Runs two microbenchmarks and prints JSON results to stdout:
- multiagent_monitor_collect: call ClusterMonitor.collect_cluster_metrics N times using a dummy lifecycle
- memory_semantic_search: call SemanticMemory.search mock N times
"""
from time import perf_counter
import json

from agent.multiagent.core.monitor import ClusterMonitor
from agent.memory.core.layers import SemanticMemory

class DummyAgent:
    def __init__(self, id):
        self.id = id
        self.state = 'RUNNING'
        self.cpu_usage = 10
        self.memory_usage = 20
        self.current_load = 0.1
        self.avg_response_time = 100
        self.task_count = 0
        self.completed_tasks = 0
        self.failed_tasks = 0

class DummyLifecycle:
    def get_all_agents(self):
        return [DummyAgent(f'a{i}') for i in range(20)]

class MockSemanticMemory(SemanticMemory):
    def __init__(self):
        # avoid heavy deps; use minimal constructor
        super().__init__()
    def search(self, query, limit=5):
        # simulate light computation
        return [{'id': str(i), 'score': 1.0} for i in range(limit)]


def run_monitor_benchmark(iterations=100):
    lifecycle = DummyLifecycle()
    cm = ClusterMonitor(lifecycle=lifecycle)
    t0 = perf_counter()
    for _ in range(iterations):
        # ClusterMonitor.collect_cluster_metrics is async; call via asyncio.run
        import asyncio
        metrics = asyncio.run(cm.collect_cluster_metrics())
    t1 = perf_counter()
    return (t1 - t0) / iterations


def run_memory_benchmark(iterations=100):
    sm = MockSemanticMemory()
    t0 = perf_counter()
    for _ in range(iterations):
        _ = sm.search('test', limit=5)
    t1 = perf_counter()
    return (t1 - t0) / iterations

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--iter', type=int, default=100)
    args = p.parse_args()
    iter = args.iter
    monitor_latency = run_monitor_benchmark(iter)
    memory_latency = run_memory_benchmark(iter)
    out = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'iterations': iter,
        'monitor_avg_s': monitor_latency,
        'memory_avg_s': memory_latency
    }
    print(json.dumps(out))
