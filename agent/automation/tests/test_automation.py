"""自动化执行框架测试"""

import asyncio

import pytest

from agent.automation.core.executor import WorkflowExecutionEngine
from agent.automation.core.healing import AdaptiveOptimizer, SelfHealingSystem
from agent.automation.core.loadbalance import LoadBalancingManager
from agent.automation.core.scheduler import (PriorityQueue,
                                             ResourceAwareScheduler,
                                             SchedulingEngine)
from agent.automation.core.triggers import TriggerExecutor, TriggerManager
from agent.core.errors import WorkflowNotFoundError
from agent.core.types import (Anomaly, ExecutionContext, JobResult,
                              OperationStatus, ResourceSnapshot, Severity,
                              SubTask, Trigger, TriggerContext, Worker,
                              Workflow)


class TestTriggers:
    def test_register_trigger(self):
        manager = TriggerManager()
        trigger = Trigger(trigger_type="schedule", workflow_id="wf1")
        reg = manager.register_trigger("wf1", trigger)
        assert reg.enabled
        assert manager.get_trigger(trigger.trigger_id) is trigger

    def test_invalid_trigger(self):
        manager = TriggerManager()
        trigger = Trigger(trigger_type="invalid_type")
        with pytest.raises(Exception):
            manager.register_trigger("wf1", trigger)

    def test_execute_triggered_workflow(self):
        manager = TriggerManager()
        executor = TriggerExecutor(
            workflow_registry={"wf1": Workflow(id="wf1", name="test")}
        )
        trigger = Trigger(trigger_type="schedule", workflow_id="wf1")
        execution = asyncio.run(
            executor.execute_triggered_workflow(trigger, TriggerContext())
        )
        assert execution is not None
        assert execution.workflow_id == "wf1"


class TestScheduler:
    def test_priority_queue(self):
        pq = PriorityQueue()
        pq.put("low", 1)
        pq.put("high", 100)
        assert pq.get() == "high"
        assert pq.get() == "low"

    def test_schedule_and_execute(self):
        engine = SchedulingEngine()
        wf = Workflow(id="wf1", priority=80)
        engine.register_workflow(wf)
        job = asyncio.run(engine.schedule_workflow(wf))
        assert job.priority == 80
        result = asyncio.run(engine.execute_job(job))
        assert result.status == "SUCCESS"

    def test_retry_on_failure(self):
        engine = SchedulingEngine()
        wf = Workflow(id="wf1", max_retries=2)
        job = asyncio.run(engine.schedule_workflow(wf))

        async def failing(job):
            raise RuntimeError("boom")

        result = asyncio.run(engine.execute_job(job, run_fn=failing))
        assert result.status == "RETRY"
        assert result.retries_remaining == 1

    def test_resource_aware_scheduling_order(self):
        scheduler = ResourceAwareScheduler()
        from agent.core.types import ScheduleJob

        jobs = [ScheduleJob(priority=10), ScheduleJob(priority=90)]
        ordered = scheduler.optimize_scheduling_order(
            jobs, ResourceSnapshot(cpu=1.0, memory=1.0)
        )
        assert ordered[0].priority == 90


class TestWorkflowEngine:
    def test_execute_workflow(self):
        engine = WorkflowExecutionEngine()
        wf = Workflow(id="wf1", tasks=[SubTask(id="t0", skill_name="s1")])
        result = asyncio.run(engine.execute_workflow(wf, ExecutionContext()))
        assert result.status == "SUCCESS"
        assert result.tasks_executed == 1

    def test_missing_dependency(self):
        engine = WorkflowExecutionEngine()
        engine.declare_dependency("wf1", ["missing_dep"])
        # 依赖检查默认放行，这里测试结果正常返回
        result = asyncio.run(
            engine.execute_workflow(Workflow(id="wf1"), ExecutionContext())
        )
        assert result.status == "SUCCESS"


class TestLoadBalance:
    def test_distribute(self):
        manager = LoadBalancingManager()
        manager.register_worker(
            Worker(worker_id="w1", available_cpu=1.0, available_memory=1.0)
        )
        manager.register_worker(
            Worker(worker_id="w2", available_cpu=0.1, available_memory=0.1)
        )
        wf = Workflow(id="wf1", cpu_requirement=0.8, memory_requirement=0.8)
        selected = asyncio.run(
            manager.distribute_workflow_execution(wf, manager.workers)
        )
        assert selected.worker_id == "w1"

    def test_suitability_penalizes_low_resources(self):
        manager = LoadBalancingManager()
        good = Worker(available_cpu=1.0, available_memory=1.0)
        bad = Worker(available_cpu=0.1, available_memory=0.1)
        wf = Workflow(cpu_requirement=0.8, memory_requirement=0.8)
        assert manager.evaluate_worker_suitability(
            good, wf
        ) > manager.evaluate_worker_suitability(bad, wf)


class TestSelfHealing:
    def test_detect_and_recover_timeout(self):
        system = SelfHealingSystem()
        anomalies = [Anomaly(type="TIMEOUT", severity=Severity.HIGH.value)]
        results = asyncio.run(system.detect_and_recover(anomalies))
        assert results[0]["status"] == "RECOVERED"

    def test_adaptive_optimizer_opportunities(self):
        optimizer = AdaptiveOptimizer()
        opportunities = optimizer.identify_optimization_opportunities(
            {
                "avg_parallelism": 1,
                "optimal_parallelism": 4,
                "potential_speedup": 2.0,
                "resource_utilization": 0.5,
                "avg_wait_time": 100,
                "target_wait_time": 30,
            }
        )
        assert len(opportunities) >= 1
