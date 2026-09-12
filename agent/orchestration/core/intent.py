"""
智能编排框架 - 意图识别和解析 (Intent Recognition)

用户意图识别、参数提取与验证。

设计文档: 02_智能编排框架设计.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from agent.core.types import (
    Intent,
    IntentAnalysis,
    ParameterDef,
    ParameterSet,
)
from agent.core.errors import ParameterValidationError

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """
    用户意图识别和提取。

    基于注册的意图库（关键词 + 参数定义）进行确定性分类，
    可通过模型提供方增强语义理解。
    """

    def __init__(self, intents: Optional[List[Intent]] = None, model_provider=None):
        self.intents: List[Intent] = intents or []
        self.model_provider = model_provider

    def register_intent(self, intent: Intent) -> None:
        self.intents.append(intent)

    def tokenize(self, text: str) -> List[str]:
        """简单分词（按空白与常见标点）。"""
        import re

        # Split on whitespace only — preserve URLs and file path tokens intact.
        return re.findall(r"\S+", text)

    def extract_entities(self, tokens: List[str]) -> Dict[str, Any]:
        """从 token 中提取实体（占位实现：数字、URL、文件路径）。"""
        import re

        entities: Dict[str, Any] = {}
        full_text = " ".join(tokens)
        # numbers: integers or floats
        numbers = re.findall(r"\d+(?:\.\d+)?", full_text)
        # urls: http(s)://... up to whitespace or common punctuation
        urls = re.findall(r"https?://[^\s,，。！？、;:]+", full_text)
        # paths: Unix-style paths (simple heuristic)
        paths = re.findall(r"/[A-Za-z0-9_\-./]+", full_text)
        if numbers:
            entities["numbers"] = numbers
        if urls:
            entities["urls"] = urls
        if paths:
            entities["paths"] = paths
        return entities

    def classify_intent(self, tokens: List[str]) -> Dict[str, float]:
        """基于关键词匹配的意图分类，返回意图名到置信度的映射。"""
        if not self.intents:
            return {}
        text = "".join(tokens).lower()
        scores: Dict[str, float] = {}
        for intent in self.intents:
            hit = sum(1 for kw in intent.keywords if kw.lower() in text)
            # 关键词命中占比 + 基础分
            base = 0.3
            score = base + (hit / max(len(intent.keywords), 1)) * 0.7 if intent.keywords else base
            scores[intent.name] = min(score, 1.0)
        return scores

    def get_top_intent(self, scores: Dict[str, float]) -> str:
        if not scores:
            return ""
        return max(scores, key=scores.get)

    def get_top_n_intents(self, scores: Dict[str, float], n: int = 3) -> List[Tuple[str, float]]:
        return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def recognize_intent(self, user_input: str, session_history: Optional[List[Any]] = None) -> IntentAnalysis:
        """识别用户意图。"""
        tokens = self.tokenize(user_input)
        entities = self.extract_entities(tokens)
        intent_scores = self.classify_intent(tokens)
        primary_intent = self.get_top_intent(intent_scores)
        confidence = intent_scores.get(primary_intent, 0.0)

        parameters: Dict[str, Any] = {}
        intent_def = self.get_intent(primary_intent)
        if intent_def is not None:
            parameters = self._extract_simple_parameters(intent_def, user_input)

        return IntentAnalysis(
            primary_intent=primary_intent,
            confidence=confidence,
            alternative_intents=self.get_top_n_intents(intent_scores, n=3),
            entities=entities,
            parameters=parameters,
            context={
                "user_state": "active",
                "domain": self._infer_domain(primary_intent),
                "complexity": intent_def.complexity if intent_def else "low",
                "urgency": "normal",
            },
            requires_clarification=confidence < 0.7,
            clarification_questions=self.generate_clarification_questions(primary_intent, parameters),
        )

    def get_intent(self, name: str) -> Optional[Intent]:
        for intent in self.intents:
            if intent.name == name:
                return intent
        return None

    def _extract_simple_parameters(self, intent: Intent, user_input: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        for p in intent.required_parameters + intent.optional_parameters:
            if p.default is not None:
                params[p.name] = p.default
        return params

    @staticmethod
    def _infer_domain(intent_name: str) -> str:
        mapping = {
            "intent_analyze_data": "data",
            "intent_generate_code": "code",
            "intent_search_information": "search",
            "intent_automate_workflow": "automation",
        }
        return mapping.get(intent_name, "general")

    @staticmethod
    def generate_clarification_questions(intent_name: str, parameters: Dict[str, Any]) -> List[str]:
        missing = [k for k, v in parameters.items() if v is None]
        return [f"请提供缺失的信息：{k}" for k in missing] if missing else []


class ParameterExtractor:
    """参数提取和验证。"""

    def extract_and_validate_parameters(
        self,
        intent: Intent,
        user_input: str,
        extracted_entities: Optional[Dict[str, Any]] = None,
    ) -> ParameterSet:
        """提取并验证参数。"""
        entities = extracted_entities or {}
        parameters: Dict[str, Any] = {}
        missing_required: List[str] = []

        for param_def in intent.required_parameters:
            value = self.extract_parameter_value(param_def, user_input, entities)
            if value is None:
                missing_required.append(param_def.name)
            else:
                validation = self.validate_parameter(param_def, value)
                if not validation:
                    raise ParameterValidationError(param_def.name, "validation failed")
                parameters[param_def.name] = value

        for param_def in intent.optional_parameters:
            value = self.extract_parameter_value(param_def, user_input, entities)
            if value is not None:
                parameters[param_def.name] = value
            elif param_def.default is not None:
                parameters[param_def.name] = param_def.default

        return ParameterSet(
            parameters=parameters,
            missing_required=missing_required,
            complete=len(missing_required) == 0,
        )

    def extract_parameter_value(self, param_def: ParameterDef, user_input: str, entities: Dict[str, Any]) -> Any:
        """从输入/实体中提取参数值（简单启发式）。"""
        text = user_input
        if param_def.type == "file_or_url":
            for url in entities.get("urls", []):
                return url
            for path in entities.get("paths", []):
                return path
        if param_def.type == "text":
            return text or None
        if param_def.type == "string":
            return text or None
        if param_def.type == "string_list":
            tokens = text.split()
            return tokens if tokens else None
        if param_def.type == "boolean":
            lowered = text.lower()
            # explicit true/false indicators
            if "true" in lowered or "是" in lowered or "yes" in lowered:
                return True
            if "false" in lowered or "否" in lowered or "no" in lowered:
                return False
            # No explicit boolean found: return default (could be None) so validation handles it
            return param_def.default
        if param_def.type == "number":
            import re

            m = re.search(r"\d+(\.\d+)?", text)
            return float(m.group()) if m else None
        return param_def.default

    @staticmethod
    def validate_parameter(param_def: ParameterDef, value: Any) -> bool:
        """验证参数值类型。"""
        if value is None:
            return False
        type_checks = {
            "text": lambda v: isinstance(v, str),
            "string": lambda v: isinstance(v, str),
            "string_list": lambda v: isinstance(v, list),
            "boolean": lambda v: isinstance(v, bool),
            "number": lambda v: isinstance(v, (int, float)),
            "file_or_url": lambda v: isinstance(v, str),
        }
        checker = type_checks.get(param_def.type, lambda v: True)
        return checker(value)


__all__ = ["IntentRecognizer", "ParameterExtractor"]
