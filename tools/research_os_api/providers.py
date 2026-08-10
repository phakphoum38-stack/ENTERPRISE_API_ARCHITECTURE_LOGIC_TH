#!/usr/bin/env python3
"""Provider-agnostic AI adapters for Research OS.

The core depends only on the Provider interface. Concrete adapters use HTTP and
standard-library modules so the initial implementation remains dependency-free.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


OPENAI_API_KEY_NAMES = ("RESEARCH_OS_OPENAI_API_KEY", "OPENAI_API_KEY")
GEMINI_API_KEY_NAMES = ("RESEARCH_OS_GEMINI_API_KEY", "GEMINI_API_KEY")
ANTHROPIC_API_KEY_NAMES = (
    "RESEARCH_OS_ANTHROPIC_API_KEY",
    "ANTHROPIC_API_KEY",
)


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str
    raw: dict[str, Any]
    sources: tuple[dict[str, str], ...] = ()


class ProviderError(RuntimeError):
    pass


class AIProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        raise NotImplementedError

    def search(self, query: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        raise ProviderError(f"provider {self.name} does not support web search")


class MockProvider(AIProvider):
    name = "mock"

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or "mock-v1"
        text = f"MOCK: {prompt[:500]}"
        return ProviderResult(self.name, selected, text, {"mock": True, "system": system})

    def search(self, query: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or "mock-search-v1"
        text = f"MOCK SEARCH: {query[:500]}"
        return ProviderResult(
            self.name,
            selected,
            text,
            {"mock": True, "system": system, "web_search": False},
        )


class OpenAIResponsesProvider(AIProvider):
    """Official OpenAI Responses adapter with optional hosted web search."""

    name = "openai-responses"

    def __init__(self, *, endpoint: str, api_key: str, default_model: str):
        if not api_key.strip():
            raise ProviderError("missing OpenAI API key")
        self.endpoint = endpoint
        self.api_key = api_key
        self.default_model = default_model

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        return self._respond(prompt, system=system, model=model, web_search=False)

    def search(self, query: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        return self._respond(query, system=system, model=model, web_search=True)

    def _respond(
        self,
        input_text: str,
        *,
        system: str,
        model: str | None,
        web_search: bool,
    ) -> ProviderResult:
        selected = model or self.default_model
        payload: dict[str, Any] = {
            "model": selected,
            "input": input_text,
            "store": False,
        }
        if system:
            payload["instructions"] = system
        if web_search:
            payload["tools"] = [{"type": "web_search"}]
            payload["tool_choice"] = "auto"
            payload["include"] = ["web_search_call.action.sources"]
        raw = _post_json(
            self.endpoint,
            payload,
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        text = _responses_text(raw)
        if not text:
            raise ProviderError("OpenAI Responses API returned no output text")
        return ProviderResult(
            self.name,
            selected,
            text,
            raw,
            tuple(_responses_sources(raw)),
        )


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


def _first_env_name(*names: str) -> str | None:
    """Return only the configured variable name, never its secret value."""
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return name
    return None


def provider_credential_status() -> dict[str, dict[str, Any]]:
    """Describe provider readiness without returning credential contents."""
    aliases = {
        "openai-responses": OPENAI_API_KEY_NAMES,
        "gemini": GEMINI_API_KEY_NAMES,
        "anthropic": ANTHROPIC_API_KEY_NAMES,
    }
    status: dict[str, dict[str, Any]] = {}
    for provider, names in aliases.items():
        source = _first_env_name(*names)
        status[provider] = {
            "configured": source is not None,
            "credential_source": source,
            "secret_exposed": False,
            "supports_web_search": provider == "openai-responses",
        }
    status["local"] = {
        "configured": True,
        "credential_source": None,
        "secret_exposed": False,
        "supports_web_search": False,
    }
    return status


def _responses_text(raw: dict[str, Any]) -> str:
    direct = raw.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks: list[str] = []
    for item in raw.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict) or content.get("type") != "output_text":
                continue
            value = content.get("text")
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())
    return "\n".join(chunks)


def _responses_sources(raw: dict[str, Any]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(url: Any, title: Any = "") -> None:
        if not isinstance(url, str) or not url.strip() or url in seen:
            return
        seen.add(url)
        sources.append({"url": url, "title": str(title or url)})

    for item in raw.get("output", []):
        if not isinstance(item, dict):
            continue
        action = item.get("action")
        if isinstance(action, dict):
            for source in action.get("sources", []):
                if isinstance(source, dict):
                    add(source.get("url"), source.get("title"))
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            for annotation in content.get("annotations", []):
                if isinstance(annotation, dict) and annotation.get("type") == "url_citation":
                    add(annotation.get("url"), annotation.get("title"))
    return sources


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    if not url or not url.strip():
        raise ProviderError("provider endpoint is empty")

    retryable_statuses = {429, 500, 502, 503, 504}
    max_attempts = 4
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
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
            last_error = exc
            if exc.code not in retryable_statuses or attempt == max_attempts:
                raise ProviderError(f"provider HTTP {exc.code}: {body[:500]}") from exc

            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = float(retry_after) if retry_after else float(2 ** (attempt - 1))
            except (TypeError, ValueError):
                delay = float(2 ** (attempt - 1))
            time.sleep(min(delay, 8.0))
        except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt == max_attempts:
                raise ProviderError(f"provider request failed after {max_attempts} attempts: {exc}") from exc
            time.sleep(float(2 ** (attempt - 1)))

    raise ProviderError(f"provider request failed: {last_error}")


def build_provider(name: str | None = None) -> AIProvider:
    selected = (name or os.getenv("RESEARCH_OS_PROVIDER", "mock")).strip().lower()
    if selected == "mock":
        return MockProvider()
    if selected in {"openai-responses", "openai-search"}:
        key = _first_env(*OPENAI_API_KEY_NAMES)
        if not key:
            raise ProviderError(
                "missing OpenAI API key (set RESEARCH_OS_OPENAI_API_KEY or OPENAI_API_KEY)"
            )
        return OpenAIResponsesProvider(
            endpoint=_env_or_default(
                "RESEARCH_OS_OPENAI_RESPONSES_ENDPOINT",
                "https://api.openai.com/v1/responses",
            ),
            api_key=key,
            default_model=_env_or_default(
                "RESEARCH_OS_OPENAI_RESPONSES_MODEL",
                "gpt-5.5",
            ),
        )
    if selected in {"openai", "openai-compatible", "local"}:
        endpoint = _env_or_default(
            "RESEARCH_OS_OPENAI_ENDPOINT",
            "http://localhost:11434/v1/chat/completions",
        )
        model = _env_or_default("RESEARCH_OS_OPENAI_MODEL", "local-model")
        return OpenAICompatibleProvider(
            endpoint=endpoint,
            api_key=_first_env(*OPENAI_API_KEY_NAMES),
            default_model=model,
        )
    if selected == "anthropic":
        key = _first_env(*ANTHROPIC_API_KEY_NAMES)
        if not key:
            raise ProviderError(
                "missing Anthropic API key (set RESEARCH_OS_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY)"
            )
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
        key = _first_env(*GEMINI_API_KEY_NAMES)
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


def build_search_provider(name: str | None = None) -> AIProvider:
    """Resolve a web-search capable provider without exposing its key."""
    selected = (
        name
        or os.getenv("RESEARCH_OS_SEARCH_PROVIDER")
        or "openai-responses"
    ).strip()
    provider = build_provider(selected)
    if provider.name not in {"openai-responses", "mock"}:
        raise ProviderError(
            f"provider {provider.name} does not support hosted web search"
        )
    return provider
