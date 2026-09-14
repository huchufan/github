"""
Memory Framework - User_model Module (compat shim)
Provides UserModel and UserPreferenceModel used by tests.
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class UserPreferenceModel:
    user_id: str = ''
    prefs: Dict[str, Any] = None

    def __init__(self, user_id: str = '', prefs: Optional[Dict[str, Any]] = None):
        self.user_id = user_id
        self.prefs = prefs or {}

    def learn_user_preferences(self, sessions: list) -> Any:
        # PoC: simple aggregation
        if not sessions:
            return type('P', (), {})()
        # assume sessions contain dict-like user_preferences
        agg = {}
        for s in sessions:
            up = getattr(s, 'user_preferences', None) or getattr(s, 'user_prefs', None) or {}
            agg.update(up)
        class Profile:
            pass
        p = Profile()
        p.communication_style = agg.get('communication_style')
        p.technical_level = agg.get('technical_level')
        return p
class UserModel:
    """User_model module (PoC)"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def learn_user_preferences(self, sessions: list) -> Any:
        # delegate to UserPreferenceModel PoC
        pref_model = UserPreferenceModel()
        return pref_model.learn_user_preferences(sessions)

    def execute(self, *args, **kwargs) -> Any:
        return {"module": "user_model", "ok": True}
