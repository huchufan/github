"""
治理框架 - 约束与限制层 (Constraints & Quotas)

资源配额系统与执行时约束检查。

设计文档: 01_治理框架设计.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.core.types import Actor, Operation

logger = logging.getLogger(__name__)


@dataclass
class ConstraintViolation:
    """约束违规。"""
    type: str = ""
    limit: Any = None
    actual: Any = None
    current: Any = None
    action: str = "REJECT"  # REJECT / QUEUE / WARN


@dataclass
class ConstraintCheckResult:
    """约束检查结果。"""
    violations: List[ConstraintViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations


class ResourceQuotaManager:
    """资源配额管理。"""

    def __init__(self, quotas: Optional[Dict[str, Dict[str, Any]]] = None):
        self.quotas = quotas or {}

    def get_quota(self, level: str, resource: str) -> Any:
        """获取配额（层级：user/role/organization）。"""
        return self.quotas.get(level, {}).get(resource, None)

    def check_quota(self, level: str, resource: str, requested: float, current: float) -> bool:
        """检查是否超出配额。返回 True 表示允许。"""
        quota = self.get_quota(level, resource)
        if quota is None or quota == "unlimited":
            return True
        return current + requested <= quota

    def set_quota(self, level: str, resource: str, value: Any) -> None:
        self.quotas.setdefault(level, {})[resource] = value


class ExecutionConstraints:
    """执行时约束检查。"""

    constraints: Dict[str, Dict[str, Any]] = {
        "timeout": {
            "admin": None,       # 无限制
            "developer": 3600,   # 1 小时
            "user": 1800,        # 30 分钟
            "service": None,
            "guest": 300,
        },
        "concurrent_limit": {
            "admin": None,
            "developer": 50,
            "user": 10,
            "service": 5,
            "guest": 1,
        },
        "resource_limit": {
            "admin": None,
            "developer": "1TB RAM",
            "user": "100GB RAM",
            "service": "100GB RAM",
            "guest": "1GB RAM",
        },
    }

    def __init__(self):
        self._current_concurrent: Dict[str, int] = {}

    def check_constraints(self, operation: Operation, actor: Actor) -> ConstraintCheckResult:
        """检查执行约束。"""
        result = ConstraintCheckResult()

        timeout = self.constraints["timeout"].get(actor.role)
        if timeout and operation.estimated_duration > timeout:
            result.violations.append(
                ConstraintViolation(
                    type="timeout",
                    limit=timeout,
                    actual=operation.estimated_duration,
                    action="REJECT",
                )
            )

        current_concurrent = self._current_concurrent.get(actor.id, 0)
        limit = self.constraints["concurrent_limit"].get(actor.role)
        if limit and current_concurrent >= limit:
            result.violations.append(
                ConstraintViolation(
                    type="concurrent_limit",
                    limit=limit,
                    current=current_concurrent,
                    action="QUEUE",
                )
            )

        return result

    def acquire(self, actor_id: str) -> None:
        """占用一个并发槽位。"""
        self._current_concurrent[actor_id] = self._current_concurrent.get(actor_id, 0) + 1

    def release(self, actor_id: str) -> None:
        """释放一个并发槽位。"""
        self._current_concurrent[actor_id] = max(0, self._current_concurrent.get(actor_id, 0) - 1)


__all__ = [
    "ConstraintViolation",
    "ConstraintCheckResult",
    "ExecutionConstraints",
    "ResourceQuotaManager",
]
