"""
智能编排框架 - 条件控制和分支 (Conditional Control Flow)

条件评估引擎，支持比较、布尔逻辑、状态检查与指标条件。

设计文档: 02_智能编排框架设计.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from agent.core.types import Condition

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """条件评估和控制流。"""

    def evaluate_condition(self, condition: Condition, execution_state: Any) -> bool:
        """评估条件表达式。"""
        if condition.type == "COMPARISON":
            return self.evaluate_comparison(condition, execution_state)
        if condition.type == "BOOLEAN_LOGIC":
            return self.evaluate_boolean_logic(condition, execution_state)
        if condition.type == "STATE_CHECK":
            return self.evaluate_state_check(condition, execution_state)
        if condition.type == "METRIC_BASED":
            return self.evaluate_metric_condition(condition, execution_state)
        raise ValueError(f"Unknown condition type: {condition.type}")

    def evaluate_comparison(self, condition: Condition, execution_state: Any) -> bool:
        """比较条件。"""
        left = self.resolve_value(condition.left, execution_state)
        right = self.resolve_value(condition.right, execution_state)
        op = condition.operator

        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        if op == "in":
            return left in right
        return False

    def evaluate_boolean_logic(
        self, condition: Condition, execution_state: Any
    ) -> bool:
        """布尔逻辑（AND/OR 组合子条件）。"""
        results = [
            self.evaluate_condition(c, execution_state) for c in condition.children
        ]
        if condition.logic == "AND":
            return all(results)
        if condition.logic == "OR":
            return any(results)
        return all(results)

    def evaluate_state_check(self, condition: Condition, execution_state: Any) -> bool:
        """状态检查。"""
        value = self.resolve_value(condition.left, execution_state)
        return bool(value)

    def evaluate_metric_condition(
        self, condition: Condition, execution_state: Any
    ) -> bool:
        """指标条件（基于执行状态中的指标）。"""
        return self.evaluate_comparison(condition, execution_state)

    def resolve_value(self, value: Any, execution_state: Any) -> Any:
        """解析值：支持字符串路径引用（如 '$variables.foo'）。"""
        if isinstance(value, str) and value.startswith("$"):
            path = value.lstrip("$").split(".")
            current: Any = execution_state
            for key in path:
                if isinstance(current, dict):
                    current = current.get(key)
                else:
                    current = getattr(current, key, None)
            return current
        return value


__all__ = ["ConditionEvaluator"]
