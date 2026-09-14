"""智能编排框架测试"""

import asyncio

import pytest

from agent.core.types import (Condition, ExecutionPlan, Intent, ParameterDef,
                              ParameterSet, SubTask)
from agent.orchestration.core.condition import ConditionEvaluator
from agent.orchestration.core.dag import DAG, Node
from agent.orchestration.core.executor import (ErrorHandlingStrategy,
                                               OrchestrationEngine)
from agent.orchestration.core.intent import (IntentRecognizer,
                                             ParameterExtractor)
from agent.orchestration.core.monitor import ExecutionMonitor
from agent.orchestration.core.planner import TaskPlanner


class TestDAG:
    def test_topological_sort(self):
        dag = DAG()
        dag.add_node(Node(id="a"))
        dag.add_node(Node(id="b"))
        dag.add_node(Node(id="c"))
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        order = dag.topological_sort()
        assert order == ["a", "b", "c"]

    def test_execution_order_parallel(self):
        dag = DAG()
        dag.add_node(Node(id="a"))
        dag.add_node(Node(id="b"))
        dag.add_node(Node(id="c"))
        dag.add_edge("a", "c")
        dag.add_edge("b", "c")
        order = dag.get_execution_order()
        assert order[0] == ["a", "b"]
        assert order[1] == ["c"]

    def test_cycle_detection(self):
        dag = DAG()
        dag.add_node(Node(id="a"))
        dag.add_node(Node(id="b"))
        dag.add_edge("a", "b")
        dag.add_edge("b", "a")
        assert dag.has_cycle()

    def test_critical_path(self):
        dag = DAG()
        for nid in ["a", "b", "c", "d"]:
            dag.add_node(Node(id=nid))
        dag.add_edge("a", "b")
        dag.add_edge("b", "d")
        dag.add_edge("a", "c")
        dag.add_edge("c", "d")
        path = dag.find_critical_path()
        assert path[0] == "a" and path[-1] == "d" and len(path) == 3


class TestIntent:
    def _make_recognizer(self):
        intents = [
            Intent(
                name="intent_generate_code",
                keywords=["写", "生成", "实现"],
                complexity="high",
                required_parameters=[ParameterDef(name="requirements", type="text")],
            ),
            Intent(
                name="intent_search_information",
                keywords=["搜索", "查找"],
                complexity="low",
            ),
        ]
        return IntentRecognizer(intents=intents)

    def test_classify_intent(self):
        rec = self._make_recognizer()
        analysis = rec.recognize_intent("帮我写一个排序算法")
        assert analysis.primary_intent == "intent_generate_code"

    def test_parameter_extraction(self):
        rec = self._make_recognizer()
        intent = rec.get_intent("intent_generate_code")
        extractor = ParameterExtractor()
        result = extractor.extract_and_validate_parameters(intent, "写一个函数", {})
        assert result.complete
        assert "requirements" in result.parameters


class TestPlanner:
    def test_plan_execution(self):
        intent = Intent(
            name="intent_analyze_data",
            skills_involved=["data:load", "data:analyze", "data:visualize"],
        )
        planner = TaskPlanner()
        plan = planner.plan_execution(
            intent, ParameterSet(parameters={"data_source": "x.csv"})
        )
        assert len(plan.subtasks) == 3
        assert plan.execution_order
        assert plan.time_estimate == 3 * 60.0


class TestExecutor:
    def test_orchestrate_execution_success(self):
        def skill(params, context):
            return {"ok": True, "skill": params}

        engine = OrchestrationEngine(
            skill_registry={
                "s1": skill,
                "s2": skill,
            }
        )
        plan = ExecutionPlan(
            subtasks=[
                SubTask(id="t0", skill_name="s1"),
                SubTask(id="t1", skill_name="s2", depends_on=["t0"]),
            ],
            execution_order=[
                [SubTask(id="t0", skill_name="s1")],
                [SubTask(id="t1", skill_name="s2", depends_on=["t0"])],
            ],
        )
        result = asyncio.run(engine.orchestrate_execution(plan))
        assert result.status == "SUCCESS"
        assert result.tasks_executed == 2

    def test_error_strategy_categorize(self):
        strategy = ErrorHandlingStrategy()
        assert strategy.categorize_error(asyncio.TimeoutError()) == "TIMEOUT"


class TestCondition:
    def test_comparison(self):
        ev = ConditionEvaluator()
        cond = Condition(type="COMPARISON", left=5, right=3, operator=">")
        assert ev.evaluate_condition(cond, {}) is True

    def test_boolean_logic(self):
        ev = ConditionEvaluator()
        cond = Condition(
            type="BOOLEAN_LOGIC",
            logic="AND",
            children=[
                Condition(type="COMPARISON", left=1, right=1, operator="=="),
                Condition(type="COMPARISON", left=2, right=1, operator=">"),
            ],
        )
        assert ev.evaluate_condition(cond, {}) is True


class TestMonitor:
    def test_progress(self):
        from agent.core.types import ExecutionState, TaskResult

        plan = ExecutionPlan(subtasks=[SubTask(id="t0"), SubTask(id="t1")])
        state = ExecutionState(
            plan=plan, tasks_completed=[TaskResult(task_id="t0", success=True)]
        )
        monitor = ExecutionMonitor()
        metrics = monitor.monitor_execution(state)
        assert metrics.overall_progress == 50.0
