#!/usr/bin/env python3
"""Secret-safe provider readiness checks for Research OS."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ProviderReadiness:
    provider: str
    ready: bool
    missing: list[str]
    endpoint_configured: bool
    model_configured: bool


REQUIREMENTS = {
    "mock": (),
    "openai-compatible": (
        "RESEARCH_OS_OPENAI_API_KEY",
        "RESEARCH_OS_OPENAI_ENDPOINT",
        "RESEARCH_OS_OPENAI_MODEL",
    ),
    "local": ("RESEARCH_OS_OPENAI_ENDPOINT", "RESEARCH_OS_OPENAI_MODEL"),
    "anthropic": ("RESEARCH_OS_ANTHROPIC_API_KEY", "RESEARCH_OS_ANTHROPIC_MODEL"),
    "gemini": ("RESEARCH_OS_GEMINI_API_KEY", "RESEARCH_OS_GEMINI_MODEL"),
}


def inspect_provider(provider: str) -> dict[str, object]:
    selected = provider.lower()
    if selected not in REQUIREMENTS:
        raise ValueError(f"unsupported provider: {selected}")
    missing = [name for name in REQUIREMENTS[selected] if not os.getenv(name)]
    if selected in {"openai-compatible", "local"}:
        endpoint_key, model_key = "RESEARCH_OS_OPENAI_ENDPOINT", "RESEARCH_OS_OPENAI_MODEL"
    elif selected == "anthropic":
        endpoint_key, model_key = "RESEARCH_OS_ANTHROPIC_ENDPOINT", "RESEARCH_OS_ANTHROPIC_MODEL"
    elif selected == "gemini":
        endpoint_key, model_key = "RESEARCH_OS_GEMINI_ENDPOINT_TEMPLATE", "RESEARCH_OS_GEMINI_MODEL"
    else:
        endpoint_key = model_key = ""
    result = ProviderReadiness(
        provider=selected,
        ready=not missing,
        missing=missing,
        endpoint_configured=True if selected == "mock" else bool(os.getenv(endpoint_key)),
        model_configured=True if selected == "mock" else bool(os.getenv(model_key)),
    )
    return asdict(result)


def inspect_all() -> dict[str, object]:
    providers = [inspect_provider(name) for name in REQUIREMENTS]
    return {
        "active": os.getenv("RESEARCH_OS_PROVIDER", "mock"),
        "providers": providers,
        "safe": True,
        "note": "Secret values are never returned.",
    }


def main() -> int:
    report = inspect_all()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    active = str(report["active"]).lower()
    active_status = next(item for item in report["providers"] if item["provider"] == active)
    return 0 if active_status["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
