from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Node:
    id: str
    name: str = ""
    task_type: str = "task"
    params: Dict = None
