#!/usr/bin/env python3
"""Run a minimal live-provider smoke test without printing prompts, replies, or secrets."""

from __future__ import annotations

import json
import os
import re
import time

from provider_readiness import inspect_provider
from providers import ProviderError, build_provider


_SECRET_ENV_NAMES = (
    "RESEARCH_OS_OPENAI_API_KEY",
    "RESEARCH_OS_ANTHROPIC_API_KEY",
    "RESEARCH_OS_GEMINI_API_KEY",
)


def _safe_error_message(exc: Exception) -> str:
    """Return a useful diagnostic while redacting known credentials."""
    message = str(exc)
    for env_name in _SECRET_ENV_NAMES:
        secret = os.getenv(env_name, "")
        if secret:
            message = message.replace(secret, "***")

    # Redact bearer tokens or API-key-like values that may appear in provider bodies.
    message = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._-]+", r"\1***", message)
    message = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "sk-***", message)
    return message[:500]


def main() -> int:
    provider_name = os.getenv("RESEARCH_OS_PROVIDER", "mock").lower()
    readiness = inspect_provider(provider_name)
    if not readiness["ready"]:
        print(json.dumps({"provider": provider_name, "ready": False, "missing": readiness["missing"]}, indent=2))
        return 2

    started = time.monotonic()
    try:
        result = build_provider(provider_name).generate(
            "Reply with exactly READY.",
            system="This is a connectivity smoke test. Do not include secrets or extra text.",
        )
    except ProviderError as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000)
        print(json.dumps({
            "provider": provider_name,
            "ready": True,
            "connected": False,
            "error_type": type(exc).__name__,
            "error": _safe_error_message(exc),
            "elapsed_ms": elapsed_ms,
            "secret_safe": True,
        }, indent=2))
        return 1

    elapsed_ms = round((time.monotonic() - started) * 1000)
    print(json.dumps({
        "provider": result.provider,
        "model": result.model,
        "ready": True,
        "connected": True,
        "response_received": bool(result.text.strip()),
        "elapsed_ms": elapsed_ms,
        "secret_safe": True,
    }, indent=2))
    return 0 if result.text.strip() else 1


if __name__ == "__main__":
    raise SystemExit(main())
