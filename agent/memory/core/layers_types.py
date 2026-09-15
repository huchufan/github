from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class KnowledgeItem:
    title: str
    content: str
    category: str = ""
    concepts: List[str] = None
    knowledge_id: Optional[str] = None


@dataclass
class SessionRecord:
    session_id: str
    user_id: str
    created_at: datetime
