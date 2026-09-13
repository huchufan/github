"""
Memory Framework - User_model Module (compat shim)
Provides UserModel and UserPreferenceModel used by tests.
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class UserPreferenceModel:
    user_id: str
    prefs: Dict[str, Any]

class UserModel:
    """User_model module (PoC)"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs) -> Any:
        return {"module": "user_model", "ok": True}

__all__ = ['UserModel', 'UserPreferenceModel']
