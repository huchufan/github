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
