"""
Governance Framework - Audit Module (compat shim + PoC)
Provides minimal AuditLogger/AuditAnalyzer/ComplianceReport/AnomalyReport
and an Audit PoC object used by some tests.
"""
from typing import Any, Dict, List
from dataclasses import dataclass

@dataclass
class ComplianceReport:
    summary: str
    details: List[str]

@dataclass
class AnomalyReport:
    summary: str
    reason: str

class AuditLogger:
    def __init__(self):
        self.events = []
        self.records = []
        self.immutable_log = []
        self.alerts = []

    def log(self, evt: Dict[str, Any]):
        self.events.append(evt)
        # produce a record dict for tests
        record = {
            'op': evt.get('op'),
            'actor': evt.get('actor'),
            'resource': evt.get('resource'),
            'result': evt.get('result'),
            'action': evt.get('action'),
        }
        self.records.append(record)
        self.immutable_log.append(record)
        if getattr(evt.get('result', {}), 'status', None) == 'FAILURE':
            self.alerts.append({'level': 'ERROR', 'record': record})
        return record

    def log_operation(self, op, actor, resource, action, result, ctx):
        evt = {
            'op': op,
            'actor': actor,
            'resource': resource,
            'action': action,
            'result': result,
            'ctx': ctx,
        }
        return self.log(evt)

    def should_alert(self, record: Dict[str, Any]) -> bool:
        """Determine whether a record warrants an alert.

        PoC heuristic:
        - alert when resource.classification is CONFIDENTIAL/SECRET/TOP_SECRET
        - alert when result.status == 'FAILURE'
        """
        if not record:
            return False
        res = record.get('resource')
        if res is not None:
            classification = getattr(res, 'classification', None)
            if classification in ('CONFIDENTIAL', 'SECRET', 'TOP_SECRET'):
                return True
        result = record.get('result')
        if result is not None and getattr(result, 'status', None) == 'FAILURE':
            return True
        return False

class AuditAnalyzer:
    def __init__(self, logger: AuditLogger | None = None):
        self.logger = logger or AuditLogger()

    def analyze(self, events: List[Dict[str, Any]]):
        # very small heuristic
        anomalies = []
        for e in events:
            if e.get('severity', 0) > 5:
                anomalies.append(e)
        return AnomalyReport(summary=f"{len(anomalies)} anomalies", reason="heuristic")

    def detect_privilege_escalation(self, records: List[Dict[str, Any]]):
        anomalies = []
        for r in records:
            actor = r.get('actor')
            if getattr(actor, 'role', None) == 'guest' and getattr(r.get('resource'), 'classification', None) != 'PUBLIC':
                anomalies.append(AnomalyReport(summary='privilege escalation', reason='guest accessed protected resource'))
        return anomalies

    def generate_compliance_report(self, start, end, policy_id):
        # naive: no events -> zero coverage
        return ComplianceReport(summary='empty', details=[])

class Audit:
    def __init__(self):
        self.config = {}
        self.logger = AuditLogger()

    def record_event(self, evt: Dict[str, Any]):
        self.logger.log(evt)

    def execute(self, *args, **kwargs):
        return {"module": "audit", "ok": True}

__all__ = ['Audit', 'AuditLogger', 'AuditAnalyzer', 'ComplianceReport', 'AnomalyReport']