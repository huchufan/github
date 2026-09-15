"""
记忆系统 - 用户建模 (User Modeling)

用户偏好学习与个人化用户建模。

设计文档: 03_记忆系统架构.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from agent.core.types import (
    CapabilityProfile,
    ComprehensiveUserModel,
    SessionRecord,
    UserHistory,
    UserProfile,
)

logger = logging.getLogger(__name__)


class UserPreferenceModel:
    """用户偏好学习和适应。"""

    def learn_user_preferences(self, session_history: List[SessionRecord]) -> UserProfile:
        """从会话历史学习用户偏好。"""
        profile = UserProfile()

        if not session_history:
            return profile

        # 偏好 1: 通信风格（从已存储的偏好聚合）
        styles = [s.user_preferences.get("communication_style") for s in session_history]
        profile.communication_style = self._most_common([s for s in styles if s]) or "neutral"

        # 偏好 2: 技术水平
        levels = [s.user_preferences.get("technical_level") for s in session_history]
        profile.technical_level = self._most_common([l for l in levels if l]) or "intermediate"

        # 偏好 3: 语言
        langs = [s.user_preferences.get("language") for s in session_history]
        profile.response_speed_preference = self._most_common([l for l in langs if l]) or "zh"

        # 偏好 4: 话题兴趣（从摘要中提取）
        topics = self._extract_topics(session_history)
        profile.interested_topics = topics[:10]

        # 偏好 5: 消息长度（verbosity）
        lengths = [s.message_count for s in session_history if s.message_count]
        profile.verbosity = (sum(lengths) / len(lengths) / 100) if lengths else 0.5

        return profile

    @staticmethod
    def _most_common(items: List[str]) -> str:
        from collections import Counter

        return Counter(items).most_common(1)[0][0] if items else ""

    @staticmethod
    def _extract_topics(sessions: List[SessionRecord]) -> List[str]:
        import re

        topics: List[str] = []
        for s in sessions:
            words = re.findall(r"[\w\u4e00-\u9fff]{2,}", s.summary)
            topics.extend(words)
        from collections import Counter

        return [w for w, _ in Counter(topics).most_common(10)]


class UserModel:
    """个人化用户建模。"""

    def __init__(self, preference_model: UserPreferenceModel | None = None):
        self.preference_model = preference_model or UserPreferenceModel()

    def build_comprehensive_user_model(self, user_history: UserHistory) -> ComprehensiveUserModel:
        """构建综合用户模型。"""
        sessions = user_history.sessions
        model = ComprehensiveUserModel(user_id=user_history.user_id)
        model.capability_profile = self.model_user_capabilities(user_history)
        model.preference_profile = self.preference_model.learn_user_preferences(sessions)
        model.knowledge_profile = self.model_user_knowledge(user_history)
        model.behavioral_profile = self.model_user_behavior(user_history)
        model.values_and_goals = self.infer_values_and_goals(user_history)
        return model

    def model_user_capabilities(self, user_history: UserHistory) -> CapabilityProfile:
        """建模用户能力。"""
        profile = CapabilityProfile()
        domains = self._analyze_domain_performance(user_history)
        profile.strong_domains = [d for d, s in domains.items() if s > 0.7]
        profile.weak_domains = [d for d, s in domains.items() if s < 0.3]
        profile.learning_speed = self._estimate_learning_speed(user_history)
        return profile

    @staticmethod
    def _analyze_domain_performance(history: UserHistory) -> Dict[str, float]:
        # 简化：从会话语言推断领域偏好
        from collections import Counter

        counter: Counter = Counter()
        for s in history.sessions:
            counter.update(s.summary.split())
        total = sum(counter.values()) or 1
        return {w: min(1.0, c / total * 5) for w, c in counter.most_common(5)}

    @staticmethod
    def _estimate_learning_speed(history: UserHistory) -> float:
        return 0.5

    def model_user_knowledge(self, history: UserHistory) -> Dict[str, Any]:
        return {"topics": [s.summary[:30] for s in history.sessions[:5]]}

    def model_user_behavior(self, history: UserHistory) -> Dict[str, Any]:
        return {"session_count": len(history.sessions)}

    def infer_values_and_goals(self, history: UserHistory) -> Dict[str, Any]:
        goals: List[str] = []
        for s in history.sessions:
            goals.extend(s.session_goals)
        return {"goals": list(dict.fromkeys(goals))}


__all__ = ["UserPreferenceModel", "UserModel"]
