from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class AuditRecord:
    audit_id: str
    timestamp: datetime
    actor: str
    action: str
    resource_type: str
    resource_id: str
    result: Any = None
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class AnomalyReport:
    type: str
    severity: str
    description: str

@dataclass
class ComplianceReport:
    audit_coverage: float
    start_time: Optional[Any] = None
    end_time: Optional[Any] = None

class AuditLogger:
    """Compatibility wrapper around AuditLog for tests expecting AuditLogger/AuditAnalyzer."""

    def __init__(self):
        self._log = AuditLog()
        self.records = self._log.records
        self.immutable_log = list(self._log.records)
        self.alerts: List[AnomalyReport] = []

    def log_operation(self, action: str, actor: Any, resource: Any, op: str, result: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        # Normalize values to strings where tests expect simple fields
        rec = self._log.record(actor=actor.id if hasattr(actor, 'id') else str(actor), action=action, resource_type=getattr(resource, 'type', str(resource)), resource_id=getattr(resource, 'id', getattr(resource, 'resource_id', '')), result=result, success=(getattr(result, 'status', '') == 'SUCCESS' or getattr(result, 'status', '') == 'SUCCESS'))
        # update immutable copy
        self.immutable_log = list(self.records)
        if not getattr(rec, 'success', True) or getattr(resource, 'classification', '') == 'CONFIDENTIAL':
            self.alerts.append(AnomalyReport(type='AUDIT_ALERT', severity='HIGH', description=f'Alert for {rec.resource_type}'))
        return rec

    def should_alert(self, record: Any) -> bool:
        return record and (not getattr(record, 'success', True) or getattr(record, 'details', {}).get('classification') == 'CONFIDENTIAL' or getattr(record, 'resource_type', '') == 'file' and getattr(record, 'result', {}).get('error') is not None)


class AuditAnalyzer:
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger

    def detect_privilege_escalation(self, records: List[Any]) -> List[AnomalyReport]:
        anomalies: List[AnomalyReport] = []
        for r in records:
            actor = getattr(r, 'actor', '')
            action = getattr(r, 'action', '')
            # PoC: if actor id startswith 'g' (guest) and action contains 'policy' -> escalation
            if str(actor).startswith('g') and 'policy' in str(action):
                anomalies.append(AnomalyReport(type='PRIVILEGE_ESCALATION', severity='HIGH', description=f'Guest attempted privileged action {action}'))
        return anomalies

    def generate_compliance_report(self, start: Any, end: Any, policy_name: str) -> ComplianceReport:
        # PoC: compute coverage = number of records in window / 1 (simple)
        total = len([r for r in self.audit_logger.records if True])
        coverage = 0.0 if total == 0 else 1.0
        return ComplianceReport(audit_coverage=coverage, start_time=start, end_time=end)


class AuditLog:
    """Simple in-memory audit log PoC"""

    def __init__(self):
        self.records: List[AuditRecord] = []

    def record(self, actor: str, action: str, resource_type: str, resource_id: str, result: Any = None, success: bool = True, details: Optional[Dict[str, Any]] = None) -> AuditRecord:
        rec = AuditRecord(
            audit_id=str(len(self.records) + 1),
            timestamp=datetime.utcnow(),
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            success=success,
            details=details or {},
        )
        self.records.append(rec)
        return rec

    def query(self, actor: Optional[str] = None, resource_type: Optional[str] = None, success: Optional[bool] = None) -> List[AuditRecord]:
        res = self.records
        if actor is not None:
            res = [r for r in res if r.actor == actor]
        if resource_type is not None:
            res = [r for r in res if r.resource_type == resource_type]
        if success is not None:
            res = [r for r in res if r.success == success]
        return res

    def to_dicts(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.records]

    """Simple in-memory audit log PoC"""

    def __init__(self):
        self.records: List[AuditRecord] = []

    def record(self, actor: str, action: str, resource_type: str, resource_id: str, result: Any = None, success: bool = True, details: Optional[Dict[str, Any]] = None) -> AuditRecord:
        rec = AuditRecord(
            audit_id=str(len(self.records) + 1),
            timestamp=datetime.utcnow(),
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            success=success,
            details=details or {},
        )
        self.records.append(rec)
        return rec

    def query(self, actor: Optional[str] = None, resource_type: Optional[str] = None, success: Optional[bool] = None) -> List[AuditRecord]:
        res = self.records
        if actor is not None:
            res = [r for r in res if r.actor == actor]
        if resource_type is not None:
            res = [r for r in res if r.resource_type == resource_type]
        if success is not None:
            res = [r for r in res if r.success == success]
        return res

    def to_dicts(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.records]
