from dataclasses import dataclass
from typing import List

@dataclass
class ComplianceReport:
    summary: str
    details: List[str]
    audit_coverage: float = 0.0
