"""
治理框架 - 监控与告警层 (Monitoring & Alerting)

治理层实时监控与多渠道告警。

设计文档: 01_治理框架设计.md
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.core.types import Severity, now

logger = logging.getLogger(__name__)


@dataclass
class GovernanceAlert:
    """治理告警。"""

    timestamp: Any = field(default_factory=now)
    level: str = Severity.MEDIUM.value
    category: str = ""
    operation: Any = None
    recommended_action: str = ""


class GovernanceMonitor:
    """治理层实时监控。"""

    RECOMMENDED_ACTIONS: Dict[str, str] = {
        "PRIVILEGE_ABUSE": "Revoke access and review actor credentials",
        "ANOMALY": "Investigate unusual activity pattern",
        "QUOTA_EXCEEDED": "Review quota allocation or request increase",
        "COMPLIANCE_VIOLATION": "Remediate violation and file compliance report",
    }

    def __init__(self, audit_analyzer=None):
        self.audit_analyzer = audit_analyzer
        self.alerts: List[GovernanceAlert] = []
        self._notify_handlers: List[Any] = []

    def register_notify_handler(self, handler) -> None:
        """注册通知处理器（如 email/slack 适配器）。"""
        self._notify_handlers.append(handler)

    def monitor_operations(self, operations: List[Any]) -> List[GovernanceAlert]:
        """对一批操作执行监控检查（单次扫描，便于测试）。"""
        raised: List[GovernanceAlert] = []
        for op in operations:
            for check_name, category in (
                ("detect_privilege_abuse", "PRIVILEGE_ABUSE"),
                ("detect_anomaly", "ANOMALY"),
                ("check_quota_exceeded", "QUOTA_EXCEEDED"),
                ("check_compliance_violation", "COMPLIANCE_VIOLATION"),
            ):
                level = getattr(self, check_name)(op)
                if level:
                    raised.append(self.raise_alert(level, category, op))
        return raised

    def detect_privilege_abuse(self, op: Any) -> Optional[str]:
        if getattr(op, "actor_role", "") in ("guest", "user"):
            action = getattr(op, "action", "") or getattr(op, "operation_type", "")
            if action in ("config:modify_system", "policy:manage", "data:export"):
                return Severity.CRITICAL.value
        return None

    def detect_anomaly(self, op: Any) -> Optional[str]:
        # 单条操作简单启发式：失败且涉及敏感数据
        if getattr(op, "operation_status", "") == "FAILURE" and getattr(
            op, "involves_sensitive_data", False
        ):
            return Severity.HIGH.value
        return None

    def check_quota_exceeded(self, op: Any) -> Optional[str]:
        return None  # 配额检查由 ResourceQuotaManager 负责，此处预留

    def check_compliance_violation(self, op: Any) -> Optional[str]:
        if getattr(op, "operation_status", "") == "FAILURE":
            return Severity.HIGH.value
        return None

    def raise_alert(self, level: str, category: str, operation: Any) -> GovernanceAlert:
        """发送告警。"""
        alert = GovernanceAlert(
            level=level,
            category=category,
            operation=operation,
            recommended_action=self.RECOMMENDED_ACTIONS.get(
                category, "Review manually"
            ),
        )
        self.alerts.append(alert)
        logger.warning("Governance alert [%s] %s", level, category)

        # 多渠道通知
        if level == Severity.CRITICAL.value:
            for handler in self._notify_handlers:
                try:
                    handler(alert)
                except Exception:  # noqa: BLE001
                    logger.exception("Notify handler failed")

        return alert


__all__ = ["GovernanceMonitor", "GovernanceAlert"]
