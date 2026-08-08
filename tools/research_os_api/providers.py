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
from typing import Any, Iterator


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class ProviderChunk:
    provider: str
    model: str
    text: str
    done: bool = False


class ProviderError(RuntimeError):
    pass


class AIProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        raise NotImplementedError

    def stream(
        self,
        prompt: str,
        *,
        system: str = "",
        model: str | None = None,
        chunk_size: int = 48,
    ) -> Iterator[ProviderChunk]:
        """Yield a provider-neutral response stream.

        Providers without native streaming fall back to transport streaming:
        ``generate`` completes first and the final text is exposed as bounded
        chunks. Native adapters override this method while preserving this
        provider-neutral contract for the API and Flutter client.
        """
        result = self.generate(prompt, system=system, model=model)
        text = result.text
        size = max(1, min(int(chunk_size), 512))
        for offset in range(0, len(text), size):
            yield ProviderChunk(
                provider=result.provider,
                model=result.model,
                text=text[offset : offset + size],
            )
        yield ProviderChunk(
            provider=result.provider,
            model=result.model,
            text="",
            done=True,
        )


class MockProvider(AIProvider):
    name = "mock"

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or "mock-v1"
        text = f"MOCK: {prompt[:500]}"
        return ProviderResult(self.name, selected, text, {"mock": True, "system": system})


class OpenAICompatibleProvider(AIProvider):
    """Adapter for OpenAI-compatible chat-completions endpoints.

    This also covers Ollama when its OpenAI-compatible ``/v1/chat/completions``
    endpoint is configured.
    """

    name = "openai-compatible"

    def __init__(self, *, endpoint: str, api_key: str | None, default_model: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.default_model = default_model

    def _messages(self, prompt: str, system: str) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or self.default_model
        payload = {
            "model": selected,
            "messages": self._messages(prompt, system),
            "temperature": 0.1,
        }
        raw = _post_json(self.endpoint, payload, self._headers())
        try:
            text = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"invalid OpenAI-compatible response: {exc}") from exc
        return ProviderResult(self.name, selected, str(text), raw)

    def stream(
        self,
        prompt: str,
        *,
        system: str = "",
        model: str | None = None,
        chunk_size: int = 48,
    ) -> Iterator[ProviderChunk]:
        selected = model or self.default_model
        payload = {
            "model": selected,
            "messages": self._messages(prompt, system),
            "temperature": 0.1,
            "stream": True,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    try:
                        delta = event["choices"][0].get("delta", {})
                        text = delta.get("content") or ""
                    except (KeyError, IndexError, TypeError, AttributeError):
                        text = ""
                    event_model = str(event.get("model") or selected)
                    if text:
                        yield ProviderChunk(self.name, event_model, str(text))
                yield ProviderChunk(self.name, selected, "", done=True)
                return
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            # Some OpenAI-compatible servers do not implement SSE. Preserve
            # compatibility by falling back to the non-streaming contract.
            try:
                yield from super().stream(
                    prompt,
                    system=system,
                    model=selected,
                    chunk_size=chunk_size,
                )
                return
            except Exception as fallback_exc:
                raise ProviderError(
                    f"OpenAI-compatible streaming failed: {exc}; fallback failed: {fallback_exc}"
                ) from fallback_exc


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

    def _payload(self, prompt: str, system: str) -> dict[str, Any]:
        combined = f"{system}\n\n{prompt}".strip() if system else prompt
        return {"contents": [{"parts": [{"text": combined}]}]}

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        selected = model or self.default_model
        endpoint = self.endpoint_template.format(model=selected, api_key=self.api_key)
        raw = _post_json(
            endpoint,
            self._payload(prompt, system),
            {"Content-Type": "application/json"},
        )
        try:
            text = raw["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"invalid Gemini response: {exc}") from exc
        return ProviderResult(self.name, selected, str(text), raw)

    def stream(
        self,
        prompt: str,
        *,
        system: str = "",
        model: str | None = None,
        chunk_size: int = 48,
    ) -> Iterator[ProviderChunk]:
        selected = model or self.default_model
        endpoint = self.endpoint_template.format(model=selected, api_key=self.api_key)
        if ":generateContent" in endpoint:
            endpoint = endpoint.replace(":generateContent", ":streamGenerateContent")
        separator = "&" if "?" in endpoint else "?"
        if "alt=sse" not in endpoint:
            endpoint = f"{endpoint}{separator}alt=sse"

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(self._payload(prompt, system)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    try:
                        parts = event["candidates"][0]["content"]["parts"]
                    except (KeyError, IndexError, TypeError):
                        parts = []
                    for part in parts if isinstance(parts, list) else []:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if text:
                                yield ProviderChunk(self.name, selected, str(text))
                yield ProviderChunk(self.name, selected, "", done=True)
                return
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            try:
                yield from super().stream(
                    prompt,
                    system=system,
                    model=selected,
                    chunk_size=chunk_size,
                )
                return
            except Exception as fallback_exc:
                raise ProviderError(
                    f"Gemini streaming failed: {exc}; fallback failed: {fallback_exc}"
                ) from fallback_exc


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
    selected = (name or os.getenv("RESEARCH_OS_PROVIDER", "mock")).lower()
    if selected == "mock":
        return MockProvider()
    if selected in {"openai", "openai-compatible", "local", "ollama"}:
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