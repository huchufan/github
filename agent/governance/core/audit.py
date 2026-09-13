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

    def log(self, evt: Dict[str, Any]):
        self.events.append(evt)

class AuditAnalyzer:
    def analyze(self, events: List[Dict[str, Any]]):
        # very small heuristic
        anomalies = []
        for e in events:
            if e.get('severity', 0) > 5:
                anomalies.append(e)
        return AnomalyReport(summary=f"{len(anomalies)} anomalies", reason="heuristic")

class Audit:
    def __init__(self):
        self.config = {}
        self.logger = AuditLogger()

    def record_event(self, evt: Dict[str, Any]):
        self.logger.log(evt)

    def execute(self, *args, **kwargs):
        return {"module": "audit", "ok": True}

__all__ = ['Audit', 'AuditLogger', 'AuditAnalyzer', 'ComplianceReport', 'AnomalyReport']
