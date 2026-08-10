#!/usr/bin/env python3
"""Secret-safe provider readiness checks for Research OS."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from providers import (
    ANTHROPIC_API_KEY_NAMES,
    GEMINI_API_KEY_NAMES,
    OPENAI_API_KEY_NAMES,
)


@dataclass(frozen=True)
class ProviderReadiness:
    provider: str
    ready: bool
    missing: list[str]
    endpoint_configured: bool
    model_configured: bool


PROVIDER_ALIASES = {
    "openai": "openai-compatible",
    "openai-search": "openai-responses",
}

REQUIREMENTS = {
    "mock": (),
    "openai-responses": (),
    "openai-compatible": (
        "RESEARCH_OS_OPENAI_ENDPOINT",
        "RESEARCH_OS_OPENAI_MODEL",
    ),
    "local": ("RESEARCH_OS_OPENAI_ENDPOINT", "RESEARCH_OS_OPENAI_MODEL"),
    "anthropic": ("RESEARCH_OS_ANTHROPIC_MODEL",),
    "gemini": ("RESEARCH_OS_GEMINI_MODEL",),
}


def canonical_provider_name(provider: str) -> str:
    selected = provider.strip().lower()
    return PROVIDER_ALIASES.get(selected, selected)


def _first_configured(names: tuple[str, ...]) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return name
    return None


def inspect_provider(provider: str) -> dict[str, object]:
    selected = canonical_provider_name(provider)
    if selected not in REQUIREMENTS:
        raise ValueError(f"unsupported provider: {selected}")

    missing = [name for name in REQUIREMENTS[selected] if not os.getenv(name)]
    if selected in {"openai-responses", "openai-compatible"} and not _first_configured(
        OPENAI_API_KEY_NAMES
    ):
        missing.extend(OPENAI_API_KEY_NAMES)
    elif selected == "anthropic" and not _first_configured(ANTHROPIC_API_KEY_NAMES):
        missing.extend(ANTHROPIC_API_KEY_NAMES)
    elif selected == "gemini" and not _first_configured(GEMINI_API_KEY_NAMES):
        missing.extend(GEMINI_API_KEY_NAMES)

    if selected == "openai-responses":
        # The official Responses endpoint and model both have safe runtime defaults.
        endpoint_configured = True
        model_configured = True
    elif selected in {"openai-compatible", "local"}:
        endpoint_configured = bool(os.getenv("RESEARCH_OS_OPENAI_ENDPOINT"))
        model_configured = bool(os.getenv("RESEARCH_OS_OPENAI_MODEL"))
    elif selected == "anthropic":
        endpoint_configured = bool(os.getenv("RESEARCH_OS_ANTHROPIC_ENDPOINT"))
        model_configured = bool(os.getenv("RESEARCH_OS_ANTHROPIC_MODEL"))
    elif selected == "gemini":
        endpoint_configured = bool(os.getenv("RESEARCH_OS_GEMINI_ENDPOINT_TEMPLATE"))
        model_configured = bool(os.getenv("RESEARCH_OS_GEMINI_MODEL"))
    else:
        endpoint_configured = True
        model_configured = True

    result = ProviderReadiness(
        provider=selected,
        ready=not missing,
        missing=missing,
        endpoint_configured=endpoint_configured,
        model_configured=model_configured,
    )
    return asdict(result)


def inspect_all() -> dict[str, object]:
    providers = [inspect_provider(name) for name in REQUIREMENTS]
    active = canonical_provider_name(os.getenv("RESEARCH_OS_PROVIDER", "mock"))
    return {
        "active": active,
        "providers": providers,
        "safe": True,
        "note": "Secret values are never returned.",
    }


def main() -> int:
    report = inspect_all()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    active = str(report["active"])
    active_status = next(item for item in report["providers"] if item["provider"] == active)
    return 0 if active_status["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
