"""多智能体框架测试"""

import asyncio

import pytest

from agent.core.types import (
    AgentConfig,
    AgentInfo,
    AgentMessage,
    AgentState,
    SubTaskResult,
    Task,
)
from agent.core.errors import (
    AgentNotFoundError,
    AgentAlreadyRegisteredError,
    InsufficientCapabilityError,
)
from agent.multiagent.core.lifecycle import AgentLifecycleManager, AgentHealthMonitor
from agent.multiagent.core.roles import AgentRoleManager
from agent.multiagent.core.communication import AgentCommunicationBus
from agent.multiagent.core.distribution import TaskDistributionManager, LoadBalancer
from agent.multiagent.core.coordination import TaskDecompositionCoordinator, ResultAggregator
from agent.multiagent.core.cluster import AgentRegistry, ClusterScaler
from agent.multiagent.core.monitor import ClusterMonitor, ClusterOptimizer


class TestLifecycle:
    def test_create_and_start(self):
        manager = AgentLifecycleManager()
        agent = asyncio.run(manager.create_agent(AgentConfig(role="WORKER", capabilities=["task_execution"])))
        assert agent.state == AgentState.INITIALIZED.value
        asyncio.run(manager.start_agent(agent.agent_id))
        assert agent.state == AgentState.RUNNING.value

    def test_stop(self):
        manager = AgentLifecycleManager()
        agent = asyncio.run(manager.create_agent(AgentConfig()))
        asyncio.run(manager.start_agent(agent.agent_id))
        asyncio.run(manager.stop_agent(agent.agent_id))
        assert agent.state == AgentState.STOPPED.value

    def test_not_found(self):
        manager = AgentLifecycleManager()
        with pytest.raises(AgentNotFoundError):
            asyncio.run(manager.get_agent("nope"))

    def test_health_check(self):
        manager = AgentLifecycleManager()
        agent = asyncio.run(manager.create_agent(AgentConfig()))
        asyncio.run(manager.start_agent(agent.agent_id))
        monitor = AgentHealthMonitor(manager)
        status = asyncio.run(monitor.perform_health_check(agent.agent_id))
        assert status.overall_health == "HEALTHY"


class TestRoles:
    def test_assign_role_insufficient_capability(self):
        manager = AgentLifecycleManager()
        agent = asyncio.run(manager.create_agent(AgentConfig(capabilities=[])))
        role_manager = AgentRoleManager(manager)
        with pytest.raises(InsufficientCapabilityError):
            asyncio.run(role_manager.assign_role(agent, "COORDINATOR"))

    def test_elect_coordinator(self):
        manager = AgentLifecycleManager()
        a1 = asyncio.run(manager.create_agent(AgentConfig(capabilities=["global_view", "task_decomposition"])))
        a1.available_cpu = 1.0
        a1.failure_rate = 0.0
        role_manager = AgentRoleManager(manager)
        elected = asyncio.run(role_manager.elect_coordinator([a1]))
        assert elected.role == "COORDINATOR"


class TestCommunication:
    def test_send_and_receive(self):
        bus = AgentCommunicationBus()
        asyncio.run(bus.send_message("a1", ["a2"], "TASK", {"x": 1}))
        messages = bus.receive_messages("a2")
        assert len(messages) == 1
        assert messages[0].message_type == "TASK"

    def test_rpc(self):
        bus = AgentCommunicationBus()
        bus.register_rpc_handler("echo", lambda params: params["value"] * 2)
        result = asyncio.run(bus.call_rpc("a1", "a2", "echo", {"value": 21}))
        assert result == 42


class TestDistribution:
    def test_distribute_task(self):
        manager = AgentLifecycleManager()
        agent = asyncio.run(manager.create_agent(AgentConfig(capabilities=["task_execution"])))
        asyncio.run(manager.start_agent(agent.agent_id))
        distributor = TaskDistributionManager(manager)
        task = Task(task_type="compute", required_skills=["task_execution"])
        assigned = asyncio.run(distributor.distribute_task(task))
        assert assigned == agent.agent_id
        assert agent.task_count == 1

    def test_load_distribution(self):
        manager = AgentLifecycleManager()
        a1 = asyncio.run(manager.create_agent(AgentConfig()))
        a2 = asyncio.run(manager.create_agent(AgentConfig()))
        a1.current_load = 1.0
        a2.current_load = 0.0
        balancer = LoadBalancer(manager)
        dist = balancer.analyze_load_distribution([a1, a2])
        assert a1.agent_id in dist.overloaded_agents
        assert a2.agent_id in dist.underloaded_agents


class TestCoordination:
    def test_decompose(self):
        coordinator = TaskDecompositionCoordinator()
        task = Task(task_type="big", decomposition_strategy="PARALLEL")
        subtasks = asyncio.run(coordinator.decompose_task(task))
        assert len(subtasks) == 3

    def test_aggregate_merge(self):
        aggregator = ResultAggregator()
        results = [
            SubTaskResult(task_id="t1", data={"a": 1}),
            SubTaskResult(task_id="t2", data={"b": 2}),
        ]
        merged = asyncio.run(aggregator.aggregate_results(results, "MERGE"))
        assert merged == {"a": 1, "b": 2}

    def test_conflict_resolution(self):
        aggregator = ResultAggregator()
        results = [
            SubTaskResult(task_id="t1", data={"x": 10}),
            SubTaskResult(task_id="t2", data={"x": 20}),
        ]
        merged = asyncio.run(aggregator.aggregate_results(results, "MERGE"))
        assert merged["x"] == 15  # 数值冲突取平均


class TestCluster:
    def test_register_and_discover(self):
        registry = AgentRegistry()
        info = AgentInfo(id="a1", role="WORKER", capabilities=["task_execution"], state="RUNNING")
        asyncio.run(registry.register_agent(info))
        discovered = asyncio.run(registry.discover_agents(role="WORKER"))
        assert len(discovered) == 1

    def test_duplicate_registration(self):
        registry = AgentRegistry()
        info = AgentInfo(id="a1", role="WORKER")
        asyncio.run(registry.register_agent(info))
        with pytest.raises(AgentAlreadyRegisteredError):
            asyncio.run(registry.register_agent(info))

    def test_scale_up(self):
        manager = AgentLifecycleManager()
        scaler = ClusterScaler(manager)
        created = asyncio.run(scaler.scale_up(2))
        assert len(created) == 2

    def test_cluster_monitor(self):
        manager = AgentLifecycleManager()
        agent = asyncio.run(manager.create_agent(AgentConfig()))
        asyncio.run(manager.start_agent(agent.agent_id))
        agent.cpu_usage = 95
        monitor = ClusterMonitor(manager)
        metrics = asyncio.run(monitor.collect_cluster_metrics())
        assert metrics.total_agents == 1
        anomalies = monitor.detect_anomalies(metrics)
        assert any(a.type == "HIGH_RESOURCE_USAGE" for a in anomalies)
