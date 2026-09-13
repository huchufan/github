from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class Node:
    id: str
    name: str = ''
    task_type: str = "task"
    params: Dict = None
