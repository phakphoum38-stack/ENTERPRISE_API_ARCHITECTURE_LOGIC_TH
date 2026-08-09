#!/usr/bin/env python3
"""Research OS AI Gateway v2 provider discovery and resolution.

The gateway separates provider *detection* from provider *selection* and never
returns credential values. Explicit configuration always wins. Automatic local
probing is skipped in CI to keep test/build behavior deterministic.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Callable


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    kind: str
    requires_credential: bool
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    state: str
    source: str
    ready: bool
    credential_present: bool
    endpoint: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class ProviderResolution:
    provider: str
    source: str
    reason: str


PROVIDER_REGISTRY: tuple[ProviderDescriptor, ...] = (
    ProviderDescriptor("mock", "builtin", False, ("chat",)),
    ProviderDescriptor("local", "openai-compatible", False, ("chat", "tools")),
    ProviderDescriptor("openai-compatible", "remote", True, ("chat", "tools")),
    ProviderDescriptor("gemini", "remote", True, ("chat", "vision", "tools")),
    ProviderDescriptor("anthropic", "remote", True, ("chat", "vision", "tools")),
)


_ENV_CREDENTIALS: dict[str, tuple[str, ...]] = {
    "gemini": ("RESEARCH_OS_GEMINI_API_KEY", "GEMINI_API_KEY"),
    "anthropic": ("RESEARCH_OS_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    "openai-compatible": ("RESEARCH_OS_OPENAI_API_KEY", "OPENAI_API_KEY"),
}


def _truthy(value: str | None) -> bool:
    return bool(value and value.strip().lower() in {"1", "true", "yes", "on"})


def _has_any_env(names: tuple[str, ...]) -> bool:
    return any(bool(os.getenv(name, "").strip()) for name in names)


def _probe_url(url: str, *, timeout: float = 0.25) -> bool:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= int(getattr(response, "status", 200)) < 500
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False


def local_discovery_enabled() -> bool:
    """Return whether localhost provider probing should run.

    CI is opt-out by default so a random service on a runner cannot change the
    selected provider. Users can explicitly override with
    RESEARCH_OS_ENABLE_LOCAL_PROVIDER_DISCOVERY.
    """
    override = os.getenv("RESEARCH_OS_ENABLE_LOCAL_PROVIDER_DISCOVERY")
    if override is not None:
        return _truthy(override)
    return not _truthy(os.getenv("CI"))


def inspect_providers(*, probe: Callable[[str], bool] | None = None) -> list[ProviderStatus]:
    probe = probe or _probe_url
    statuses: list[ProviderStatus] = [
        ProviderStatus(
            provider="mock",
            state="available",
            source="builtin",
            ready=True,
            credential_present=False,
            reason="deterministic fallback provider",
        )
    ]

    local_endpoint = os.getenv("RESEARCH_OS_OPENAI_ENDPOINT", "").strip()
    explicit_local = bool(local_endpoint) and local_endpoint.startswith(
        ("http://127.0.0.1", "http://localhost", "https://127.0.0.1", "https://localhost")
    )
    local_ready = False
    local_source = "not-detected"
    endpoint: str | None = None
    if explicit_local:
        endpoint = local_endpoint
        local_ready = True
        local_source = "environment"
    elif local_discovery_enabled():
        ollama_probe = "http://127.0.0.1:11434/api/tags"
        if probe(ollama_probe):
            endpoint = "http://127.0.0.1:11434/v1/chat/completions"
            local_ready = True
            local_source = "localhost-probe"

    statuses.append(
        ProviderStatus(
            provider="local",
            state="available" if local_ready else "offline",
            source=local_source,
            ready=local_ready,
            credential_present=False,
            endpoint=endpoint,
            reason="local OpenAI-compatible endpoint detected" if local_ready else "no local endpoint detected",
        )
    )

    for provider in ("gemini", "anthropic", "openai-compatible"):
        credential_present = _has_any_env(_ENV_CREDENTIALS[provider])
        statuses.append(
            ProviderStatus(
                provider=provider,
                state="available" if credential_present else "needs_setup",
                source="environment" if credential_present else "not-configured",
                ready=credential_present,
                credential_present=credential_present,
                reason="credential detected" if credential_present else "credential not configured",
            )
        )
    return statuses


def resolve_provider(*, probe: Callable[[str], bool] | None = None) -> ProviderResolution:
    """Resolve the active provider without leaking secrets.

    Precedence:
    1. Explicit RESEARCH_OS_PROVIDER value (except ``auto``)
    2. Ready local provider (local-first policy)
    3. Gemini
    4. Anthropic
    5. OpenAI-compatible
    6. Built-in mock fallback
    """
    explicit = os.getenv("RESEARCH_OS_PROVIDER", "").strip().lower()
    if explicit and explicit != "auto":
        known = {item.name for item in PROVIDER_REGISTRY}
        aliases = {"openai": "openai-compatible"}
        selected = aliases.get(explicit, explicit)
        if selected not in known:
            return ProviderResolution(selected, "explicit", "unsupported explicit provider")
        return ProviderResolution(selected, "explicit", "explicit provider configuration")

    statuses = {item.provider: item for item in inspect_providers(probe=probe)}
    for provider in ("local", "gemini", "anthropic", "openai-compatible"):
        if statuses[provider].ready:
            return ProviderResolution(provider, statuses[provider].source, "first ready provider by local-first policy")
    return ProviderResolution("mock", "builtin", "no configured provider is ready")


def gateway_report(*, probe: Callable[[str], bool] | None = None) -> dict[str, object]:
    resolution = resolve_provider(probe=probe)
    return {
        "selected": asdict(resolution),
        "providers": [asdict(item) for item in inspect_providers(probe=probe)],
        "registry": [asdict(item) for item in PROVIDER_REGISTRY],
        "safe": True,
        "note": "Credential values are never returned.",
    }
