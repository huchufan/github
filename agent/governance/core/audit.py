"""
Governance Framework - Audit Module (compat shim + PoC)
Provides AuditLogger/AuditAnalyzer/ComplianceReport/AnomalyReport and an Audit PoC.
This audit module uses the project-wide AuditRecord type from agent.core.types so tests
can assert isinstance(..., AuditRecord).
"""
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

# Reuse the canonical AuditRecord type defined in agent.core.types so tests' isinstance checks succeed.
from agent.core.types import AuditRecord

@dataclass
class ComplianceReport:
    summary: str
    details: List[str]
    audit_coverage: float = 0.0

@dataclass
class AnomalyReport:
    summary: str
    reason: str
    type: str = ''
    severity: int = 0

class AuditLogger:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.records: List[AuditRecord] = []
        self.immutable_log: List[AuditRecord] = []
        self.alerts: List[Dict[str, Any]] = []
        self._alert_handlers: List[Callable[[Dict[str, Any]], None]] = []

    def log(self, evt: Dict[str, Any]) -> AuditRecord:
        self.events.append(evt)
        # produce an AuditRecord (canonical) for tests
        rec = AuditRecord(
            audit_id=evt.get('op', '') + '-' + datetime.now().isoformat(),
            timestamp=datetime.now(),
            actor_id=getattr(evt.get('actor'), 'id', '') if evt.get('actor') else '',
            actor_role=getattr(evt.get('actor'), 'role', '') if evt.get('actor') else '',
            actor_organization=getattr(evt.get('actor'), 'organization', '') if evt.get('actor') else '',
            operation_type=evt.get('op', ''),
            operation_status=getattr(evt.get('result'), 'status', '') if evt.get('result') else '',
            resource_type=getattr(evt.get('resource'), 'type', '') if evt.get('resource') else '',
            resource_id=getattr(evt.get('resource'), 'id', '') if evt.get('resource') else '',
            resource_owner=getattr(evt.get('resource'), 'owner', '') if evt.get('resource') else '',
            action_details=evt.get('action', ''),
            source_ip=getattr(evt.get('ctx'), 'source_ip', '') if evt.get('ctx') else '',
            source_gateway=getattr(evt.get('ctx'), 'gateway', '') if evt.get('ctx') else '',
            result_code=getattr(evt.get('result'), 'code', 0) if evt.get('result') else 0,
            error_message=getattr(evt.get('result'), 'error', None) if evt.get('result') else None,
            involves_sensitive_data=bool(getattr(evt.get('resource'), 'classification', None) in ('CONFIDENTIAL', 'SECRET', 'TOP_SECRET')),
            data_classification=getattr(evt.get('resource'), 'classification', '') if evt.get('resource') else '',
            encryption_used=getattr(evt.get('ctx'), 'use_encryption', True) if evt.get('ctx') else True,
            network_security=getattr(evt.get('ctx'), 'network_security_level', '' ) if evt.get('ctx') else '',
            changes=[],
        )
        self.records.append(rec)
        self.immutable_log.append(rec)
        # Alert when the record matches alerting heuristics (sensitive data, failure, etc.)
        if self.should_alert(rec) or getattr(evt.get('result', {}), 'status', None) == 'FAILURE':
            level = 'ERROR' if getattr(evt.get('result', {}), 'status', None) == 'FAILURE' else 'WARN'
            alert = {'level': level, 'record': rec}
            self.alerts.append(alert)
            for h in list(self._alert_handlers):
                try:
                    h(alert)
                except Exception:
                    pass
        return rec

    def log_operation(self, op, actor, resource, action, result, ctx) -> AuditRecord:
        evt = {
            'op': op,
            'actor': actor,
            'resource': resource,
            'action': action,
            'result': result,
            'ctx': ctx,
        }
        return self.log(evt)

    def should_alert(self, record: AuditRecord) -> bool:
        if not record:
            return False
        if record.data_classification in ('CONFIDENTIAL', 'SECRET', 'TOP_SECRET'):
            return True
        if record.operation_status == 'FAILURE':
            return True
        return False

    def register_alert_handler(self, handler: Callable[[Dict[str, Any]], None]):
        if callable(handler):
            self._alert_handlers.append(handler)

    def unregister_alert_handler(self, handler: Callable[[Dict[str, Any]], None]):
        try:
            self._alert_handlers.remove(handler)
        except ValueError:
            pass

class AuditAnalyzer:
    def __init__(self, logger: Optional[AuditLogger] = None):
        self.logger = logger or AuditLogger()

    def analyze(self, events: List[Dict[str, Any]]):
        anomalies: List[AnomalyReport] = []
        for e in events:
            if e.get('severity', 0) > 5:
                anomalies.append(AnomalyReport(summary=str(e), reason='severity', type='SEV', severity=e.get('severity', 0)))
        return anomalies

    def detect_privilege_escalation(self, records: List[AuditRecord]):
        anomalies: List[AnomalyReport] = []
        for r in records:
            if getattr(r, 'actor_role', None) == 'guest' and getattr(r, 'data_classification', None) != 'PUBLIC':
                anomalies.append(AnomalyReport(summary='privilege escalation', reason='guest accessed protected resource', type='PRIVILEGE_ESCALATION', severity=3))
        return anomalies

    def detect_anomalies(self, time_window=None):
        """Detect generic anomalies from the logger's records in the given time window."""
        records = self.logger.records if self.logger else []
        out: List[AnomalyReport] = []
        # simple heuristics: many accesses to confidential resources or many failures
        by_actor: Dict[str, int] = {}
        for r in records:
            actor = getattr(r, 'actor_id', 'unknown')
            by_actor[actor] = by_actor.get(actor, 0) + 1
            if getattr(r, 'data_classification', None) in ('CONFIDENTIAL', 'SECRET'):
                out.append(AnomalyReport(summary='sensitive access', reason='accessed confidential resource', type='UNUSUAL_ACCESS', severity=2))
            if getattr(r, 'operation_status', None) == 'FAILURE':
                out.append(AnomalyReport(summary='operation failures', reason='failure observed', type='HIGH_FAILURE_RATE', severity=3))
        for actor, cnt in by_actor.items():
            if cnt > 50:
                out.append(AnomalyReport(summary=f'unusual access count {cnt}', reason='high access count', type='UNUSUAL_ACCESS', severity=2))
        return out

    def generate_compliance_report(self, start, end, policy_id):
        return ComplianceReport(summary='empty', details=[], audit_coverage=0.0)

class Audit:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.logger = AuditLogger()

    def record_event(self, evt: Dict[str, Any]):
        self.logger.log(evt)

    def execute(self, *args, **kwargs):
        return {"module": "audit", "ok": True}

__all__ = ['Audit', 'AuditLogger', 'AuditAnalyzer', 'ComplianceReport', 'AnomalyReport', 'AuditRecord']
