import os
import asyncio
from agent.core.models import ModelProvider, ModelConfig


def test_local_fallback_without_api_key(monkeypatch):
    # ensure env has no API key
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    prov = ModelProvider()
    resp = prov.complete("Hello world")
    assert resp.text == "Hello world"
    assert resp.usage.get('local_fallback', True) is True


def test_model_config_api_key_property(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'dummy')
    cfg = ModelConfig()
    assert cfg.api_key == 'dummy'
    # when env removed, property returns None
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    cfg2 = ModelConfig()
    assert cfg2.api_key is None
