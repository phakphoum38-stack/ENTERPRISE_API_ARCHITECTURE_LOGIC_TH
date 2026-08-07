#!/usr/bin/env python3
"""Run a minimal live-provider smoke test without printing prompts, replies, or secrets."""

from __future__ import annotations

import json
import os
import time

from provider_readiness import inspect_provider
from providers import ProviderError, build_provider


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
        print(json.dumps({"provider": provider_name, "ready": True, "connected": False, "error_type": type(exc).__name__}, indent=2))
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
