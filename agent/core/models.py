"""
Hermes Agent - 模型与配置 (Model & Configuration)

统一的模型提供方抽象与默认模型配置。默认模型为 crazyroute/gpt-5-mini，
通过 OpenRouter 兼容接口访问。该模块被所有框架复用，用于意图识别、
语义编码、技能生成等需要 LLM 能力的环节。

设计文档: 00_系统架构总览.md
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib import error as urlerror
from urllib import request

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 默认模型配置
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "crazyroute/gpt-5-mini"

DEFAULT_MODEL_CONFIG: Dict[str, Any] = {
    "model": DEFAULT_MODEL,
    "provider": "openrouter",
    "base_url": "https://openrouter.ai/api/v1",
    "temperature": 0.7,
    "max_tokens": 2048,
    "timeout": 60,
    "api_key_env": "OPENROUTER_API_KEY",
}


@dataclass
class ModelConfig:
    """模型配置。"""

    model: str = DEFAULT_MODEL
    provider: str = "openrouter"
    base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    api_key_env: str = "OPENROUTER_API_KEY"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})  # type: ignore[misc]

    @property
    def api_key(self) -> Optional[str]:
        return os.environ.get(self.api_key_env)


@dataclass
class ModelResponse:
    """模型响应。"""

    text: str = ""
    model: str = DEFAULT_MODEL
    usage: Dict[str, Any] = field(default_factory=dict)
    raw: Any = None


# ---------------------------------------------------------------------------
# 模型提供方抽象
# ---------------------------------------------------------------------------


class ModelProvider:
    """
    LLM 模型提供方客户端。

    默认使用 OpenRouter 兼容接口调用 crazyroute/gpt-5-mini。
    当未配置 API Key 或网络不可用时，`complete` 会回退到确定性的
    本地启发式实现，保证系统在无外部依赖下仍可运行与测试。
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """执行一次文本补全。失败时回退到本地实现。"""
        api_key = self.config.api_key
        if not api_key:
            logger.debug("No API key configured; using local fallback completion")
            return self._local_fallback(prompt, system)

        payload = {
            "model": self.config.model,
            "messages": [],
            "temperature": (
                temperature if temperature is not None else self.config.temperature
            ),
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        if system:
            payload["messages"].append({"role": "system", "content": system})
        payload["messages"].append({"role": "user", "content": prompt})

        try:
            req = request.Request(
                f"{self.config.base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with request.urlopen(req, timeout=self.config.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return ModelResponse(
                text=content,
                model=self.config.model,
                usage=data.get("usage", {}),
                raw=data,
            )
        except (urlerror.URLError, TimeoutError, KeyError, ValueError) as exc:
            logger.warning("Model call failed (%s); using local fallback", exc)
            return self._local_fallback(prompt, system)

    @staticmethod
    def _local_fallback(prompt: str, system: Optional[str]) -> ModelResponse:
        """确定性的本地回退，用于离线运行与测试。"""
        # 简单关键词提取，模拟结构化输出
        text = prompt.strip()
        return ModelResponse(
            text=text, model=DEFAULT_MODEL, usage={"local_fallback": True}
        )


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------

_default_provider: Optional[ModelProvider] = None


def get_model_provider(config: Optional[ModelConfig] = None) -> ModelProvider:
    """获取（或创建）全局模型提供方单例。"""
    global _default_provider
    if config is not None:
        return ModelProvider(config)
    if _default_provider is None:
        _default_provider = ModelProvider()
    return _default_provider
