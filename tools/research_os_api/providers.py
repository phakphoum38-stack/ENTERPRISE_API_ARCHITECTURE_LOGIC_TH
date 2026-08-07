#!/usr/bin/env python3
"""Provider-agnostic AI adapters for Research OS.

The core depends only on the Provider interface. Concrete adapters use HTTP and
standard-library modules so the initial implementation remains dependency-free.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str
    raw: dict[str, Any]


class ProviderError(RuntimeError):
    pass


class AIProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        raise NotImplementedError


class MockProvider(AIProvider):
    name = "mock"

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or "mock-v1"
        text = f"MOCK: {prompt[:500]}"
        return ProviderResult(self.name, selected, text, {"mock": True, "system": system})


class OpenAICompatibleProvider(AIProvider):
    """Adapter for OpenAI-compatible chat-completions endpoints."""

    name = "openai-compatible"

    def __init__(self, *, endpoint: str, api_key: str | None, default_model: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.default_model = default_model

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or self.default_model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": selected, "messages": messages, "temperature": 0.1}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        raw = _post_json(self.endpoint, payload, headers)
        try:
            text = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"invalid OpenAI-compatible response: {exc}") from exc
        return ProviderResult(self.name, selected, str(text), raw)


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, *, endpoint: str, api_key: str, default_model: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.default_model = default_model

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or self.default_model
        payload: dict[str, Any] = {
            "model": selected,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        raw = _post_json(self.endpoint, payload, headers)
        try:
            text = raw["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"invalid Anthropic response: {exc}") from exc
        return ProviderResult(self.name, selected, str(text), raw)


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, *, endpoint_template: str, api_key: str, default_model: str):
        self.endpoint_template = endpoint_template
        self.api_key = api_key
        self.default_model = default_model

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or self.default_model
        endpoint = self.endpoint_template.format(model=selected, api_key=self.api_key)
        combined = f"{system}\n\n{prompt}".strip() if system else prompt
        payload = {"contents": [{"parts": [{"text": combined}]}]}
        raw = _post_json(endpoint, payload, {"Content-Type": "application/json"})
        try:
            text = raw["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"invalid Gemini response: {exc}") from exc
        return ProviderResult(self.name, selected, str(text), raw)


def _env_or_default(name: str, default: str) -> str:
    """Return a trimmed environment value, or the default when unset/blank."""
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def _first_env(*names: str) -> str | None:
    """Return the first non-empty environment variable from ``names``."""
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    if not url or not url.strip():
        raise ProviderError("provider endpoint is empty")

    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"provider HTTP {exc.code}: {body[:500]}") from exc
    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        raise ProviderError(f"provider request failed: {exc}") from exc


def build_provider(name: str | None = None) -> AIProvider:
    selected = (name or os.getenv("RESEARCH_OS_PROVIDER", "mock")).lower()
    if selected == "mock":
        return MockProvider()
    if selected in {"openai", "openai-compatible", "local"}:
        endpoint = _env_or_default(
            "RESEARCH_OS_OPENAI_ENDPOINT",
            "http://localhost:11434/v1/chat/completions",
        )
        model = _env_or_default("RESEARCH_OS_OPENAI_MODEL", "local-model")
        return OpenAICompatibleProvider(
            endpoint=endpoint,
            api_key=os.getenv("RESEARCH_OS_OPENAI_API_KEY"),
            default_model=model,
        )
    if selected == "anthropic":
        key = os.getenv("RESEARCH_OS_ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("missing RESEARCH_OS_ANTHROPIC_API_KEY")
        return AnthropicProvider(
            endpoint=_env_or_default(
                "RESEARCH_OS_ANTHROPIC_ENDPOINT",
                "https://api.anthropic.com/v1/messages",
            ),
            api_key=key,
            default_model=_env_or_default(
                "RESEARCH_OS_ANTHROPIC_MODEL",
                "claude-sonnet-4-5",
            ),
        )
    if selected == "gemini":
        key = _first_env("RESEARCH_OS_GEMINI_API_KEY", "GEMINI_API_KEY")
        if not key:
            raise ProviderError(
                "missing Gemini API key (set RESEARCH_OS_GEMINI_API_KEY or GEMINI_API_KEY)"
            )
        return GeminiProvider(
            endpoint_template=_env_or_default(
                "RESEARCH_OS_GEMINI_ENDPOINT_TEMPLATE",
                "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            ),
            api_key=key,
            default_model=_env_or_default(
                "RESEARCH_OS_GEMINI_MODEL",
                "gemini-2.5-flash",
            ),
        )
    raise ProviderError(f"unsupported provider: {selected}")
