"""
治理框架 - 审计日志层 (Audit Trail)

完整的操作审计追踪、存储、查询与异常检测。

设计文档: 01_治理框架设计.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agent.core.types import (
    Actor,
    AuditRecord,
    ExecutionContext,
    OperationResult,
    Resource,
    Severity,
    now,
)

logger = logging.getLogger(__name__)


@dataclass
class ComplianceReport:
    """合规性报告。"""
    policy_id: str = ""
    period: Any = None
    compliance_score: float = 0.0
    violations_count: int = 0
    violation_details: List[Any] = field(default_factory=list)
    audit_coverage: float = 0.0
    log_integrity: bool = True
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AnomalyReport:
    """异常检测报告。"""
    type: str = ""
    severity: str = Severity.MEDIUM.value
    description: str = ""
    evidence: List[Any] = field(default_factory=list)


class AuditLogger:
    """
    完整的操作审计追踪系统。

    记录所有重要操作，支持多目标持久化（内存 + 不可变日志列表），
    并对敏感操作触发实时告警。
    """

    def __init__(self):
        self.records: List[AuditRecord] = []
        self.immutable_log: List[AuditRecord] = []
        self.alerts: List[Dict[str, Any]] = []
        self._alert_handlers: List[Any] = []

    def register_alert_handler(self, handler) -> None:
        """注册告警处理器（可挂载到监控/通知层）。"""
        self._alert_handlers.append(handler)

    def log_operation(
        self,
        operation_type: str,
        actor: Actor,
        resource: Resource,
        action: str,
        result: OperationResult,
        context: ExecutionContext,
        changes: Optional[List[Dict[str, Any]]] = None,
    ) -> AuditRecord:
        """记录一次操作。"""
        record = AuditRecord(
            actor_id=actor.id,
            actor_role=actor.role,
            actor_organization=actor.organization,
            operation_type=operation_type,
            operation_status=result.status,
            resource_type=resource.type,
            resource_id=resource.id,
            resource_owner=resource.owner,
            action_details=action,
            source_ip=context.source_ip,
            source_gateway=context.gateway,
            request_id=context.request_id,
            result_code=result.code,
            error_message=result.error if result.status == "FAILURE" else None,
            involves_sensitive_data=resource.classification in ("CONFIDENTIAL", "SECRET"),
            data_classification=resource.classification,
            encryption_used=context.use_encryption,
            network_security=context.network_security_level,
            changes=changes or [],
        )

        # 多目标持久化
        self.records.append(record)
        self.immutable_log.append(record)

        # 实时监控
        if self.should_alert(record):
            self.send_security_alert(record)

        return record

    def should_alert(self, record: AuditRecord) -> bool:
        """判断是否需要告警。"""
        if record.operation_status == "FAILURE":
            return True
        if record.involves_sensitive_data:
            return True
        return False

    def send_security_alert(self, record: AuditRecord) -> None:
        """发送安全告警。"""
        alert = {
            "audit_id": record.audit_id,
            "level": Severity.HIGH.value,
            "category": "AUDIT_ALERT",
            "message": f"Sensitive/failed operation {record.operation_type}",
        }
        self.alerts.append(alert)
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception:  # noqa: BLE001 - 告警处理不应中断审计
                logger.exception("Alert handler failed")

    # -- 查询 ---------------------------------------------------------------

    def query(
        self,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[AuditRecord]:
        """按条件查询审计记录。"""
        results = self.records
        if actor_id:
            results = [r for r in results if r.actor_id == actor_id]
        if resource_type:
            results = [r for r in results if r.resource_type == resource_type]
        if status:
            results = [r for r in results if r.operation_status == status]
        if since:
            results = [r for r in results if r.timestamp >= since]
        return results


class AuditAnalyzer:
    """审计数据分析和异常检测。"""

    def __init__(self, logger: AuditLogger):
        self.logger = logger

    def detect_anomalies(self, time_window: timedelta = timedelta(days=1)) -> List[AnomalyReport]:
        """检测异常操作模式。"""
        cutoff = now() - time_window
        records = [r for r in self.logger.records if r.timestamp >= cutoff]
        anomalies: List[AnomalyReport] = []

        anomalies.extend(self.detect_privilege_escalation(records))
        anomalies.extend(self.detect_unusual_access_patterns(records))
        anomalies.extend(self.detect_bulk_operations(records))
        anomalies.extend(self.detect_failure_rate_spikes(records))

        return anomalies

    def detect_privilege_escalation(self, records: List[AuditRecord]) -> List[AnomalyReport]:
        """检测权限滥用：低权限角色尝试高风险操作。"""
        high_risk = {"config:modify_system", "policy:manage", "data:export"}
        anomalies = []
        for r in records:
            if r.operation_type in high_risk and r.actor_role in ("guest", "user"):
                anomalies.append(
                    AnomalyReport(
                        type="PRIVILEGE_ESCALATION",
                        severity=Severity.CRITICAL.value,
                        description=f"{r.actor_role} attempted {r.operation_type}",
                        evidence=[r.audit_id],
                    )
                )
        return anomalies

    def detect_unusual_access_patterns(self, records: List[AuditRecord]) -> List[AnomalyReport]:
        """检测异常访问模式：单 actor 短时间内大量敏感访问。"""
        from collections import Counter

        sensitive = [r for r in records if r.involves_sensitive_data]
        counter = Counter(r.actor_id for r in sensitive)
        anomalies = []
        for actor_id, count in counter.items():
            if count > 50:
                anomalies.append(
                    AnomalyReport(
                        type="UNUSUAL_ACCESS",
                        severity=Severity.HIGH.value,
                        description=f"Actor {actor_id} accessed sensitive data {count} times",
                    )
                )
        return anomalies

    def detect_bulk_operations(self, records: List[AuditRecord]) -> List[AnomalyReport]:
        """检测批量操作。"""
        from collections import Counter

        counter = Counter(r.operation_type for r in records)
        anomalies = []
        for op_type, count in counter.items():
            if count > 200:
                anomalies.append(
                    AnomalyReport(
                        type="BULK_OPERATION",
                        severity=Severity.MEDIUM.value,
                        description=f"{count} {op_type} operations detected",
                    )
                )
        return anomalies

    def detect_failure_rate_spikes(self, records: List[AuditRecord]) -> List[AnomalyReport]:
        """检测失败率异常。"""
        if not records:
            return []
        failures = [r for r in records if r.operation_status == "FAILURE"]
        rate = len(failures) / len(records)
        if rate > 0.3:
            return [
                AnomalyReport(
                    type="HIGH_FAILURE_RATE",
                    severity=Severity.HIGH.value,
                    description=f"Failure rate {rate:.0%} exceeds 30% threshold",
                )
            ]
        return []

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        policy_id: str,
    ) -> ComplianceReport:
        """生成合规性报告。"""
        window_records = [
            r for r in self.logger.records if start_date <= r.timestamp <= end_date
        ]
        violations = [r for r in window_records if r.operation_status == "FAILURE"]
        coverage = 1.0 if window_records else 0.0
        return ComplianceReport(
            policy_id=policy_id,
            period=(start_date, end_date),
            compliance_score=1.0 - (len(violations) / len(window_records) if window_records else 0.0),
            violations_count=len(violations),
            violation_details=[r.audit_id for r in violations],
            audit_coverage=coverage,
            log_integrity=self.verify_log_integrity(),
            recommendations=self._generate_recommendations(violations),
        )

    def verify_log_integrity(self) -> bool:
        """校验日志完整性（记录与不可变日志一致）。"""
        return len(self.logger.records) == len(self.logger.immutable_log)

    @staticmethod
    def _generate_recommendations(violations: List[AuditRecord]) -> List[str]:
        if not violations:
            return ["No violations; maintain current posture."]
        types = {v.operation_type for v in violations}
        return [f"Review failure pattern in operations: {', '.join(sorted(types))}"]


__all__ = ["AuditLogger", "AuditAnalyzer", "ComplianceReport", "AnomalyReport"]
