#!/usr/bin/env python3
"""Secret-safe AI provider connection control.

The module exposes backend-only readiness and evidence for OpenAI/GPT and
Gemini. It never accepts or returns provider secrets and has no execution,
authorization, merge, or release authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

CONTRACT = "current/RESEARCH_OS_AI_PROVIDER_CONNECTION_CONTRACT.json"
PROVIDERS = {
    "openai": {
        "label": "OpenAI / GPT",
        "adapter": "openai-compatible",
        "key": "RESEARCH_OS_OPENAI_API_KEY",
        "endpoint": "RESEARCH_OS_OPENAI_ENDPOINT",
        "model": "RESEARCH_OS_OPENAI_MODEL",
    },
    "gemini": {
        "label": "Google Gemini",
        "adapter": "gemini",
        "key": "RESEARCH_OS_GEMINI_API_KEY",
        "endpoint": "RESEARCH_OS_GEMINI_ENDPOINT_TEMPLATE",
        "model": "RESEARCH_OS_GEMINI_MODEL",
    },
}


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    label: str
    state: str
    adapter: str
    credential_configured: bool
    endpoint_configured: bool
    model_configured: bool
    api_fallback_available: bool
    secret_exposed: bool = False


def _configured(name: str) -> ProviderStatus:
    if name not in PROVIDERS:
        raise ValueError(f"unsupported provider: {name}")
    provider = PROVIDERS[name]
    key_ok = bool(os.getenv(provider["key"], "").strip())
    endpoint_ok = bool(os.getenv(provider["endpoint"], "").strip()) or name == "openai"
    model_ok = bool(os.getenv(provider["model"], "").strip())
    if key_ok and model_ok:
        state = "CONNECTED"
    elif key_ok or model_ok:
        state = "DEGRADED"
    else:
        state = "NOT_CONNECTED"
    return ProviderStatus(
        name,
        provider["label"],
        state,
        provider["adapter"],
        key_ok,
        endpoint_ok,
        model_ok,
        True,
    )


def inspect() -> dict:
    items = [asdict(_configured(name)) for name in PROVIDERS]
    return {
        "contract": CONTRACT,
        "providers": items,
        "routing": {
            "primary": "PLATFORM_CONNECTOR",
            "secondary": "PLATFORM_API_FALLBACK",
        },
        "authority": "FINAL_GATE",
        "safe": all(not item["secret_exposed"] for item in items),
    }


def connect(provider: str) -> dict:
    status = asdict(_configured(provider))
    state = status["state"]
    if state == "DEGRADED":
        state = "API_FALLBACK"
        status["state"] = state
    evidence = evidence_record(
        provider=provider,
        operation="CONNECT",
        state=state,
        source_sha=os.getenv("RESEARCH_OS_SOURCE_SHA", "runtime-unpinned"),
    )
    return {
        "provider": status,
        "connection": {
            "operation": "CONNECT",
            "state": state,
            "mode": "BACKEND_READINESS_ONLY",
            "secret_exposed": False,
        },
        "evidence": evidence,
        "release_authority": "FINAL_GATE",
    }


def disconnect(provider: str) -> dict:
    status = asdict(_configured(provider))
    status["state"] = "NOT_CONNECTED"
    return {
        "provider": status,
        "connection": {
            "operation": "DISCONNECT",
            "state": "NOT_CONNECTED",
            "mode": "BACKEND_READINESS_ONLY",
            "secret_exposed": False,
        },
        "evidence": evidence_record(
            provider=provider,
            operation="DISCONNECT",
            state="NOT_CONNECTED",
            source_sha=os.getenv("RESEARCH_OS_SOURCE_SHA", "runtime-unpinned"),
        ),
        "release_authority": "FINAL_GATE",
    }


def evidence_record(
    *, provider: str, operation: str, state: str, source_sha: str
) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    raw = f"{provider}|{operation}|{state}|{source_sha}|{timestamp}".encode()
    return {
        "provider": provider,
        "operation": operation,
        "state": state,
        "source_sha": source_sha,
        "timestamp": timestamp,
        "result_hash": hashlib.sha256(raw).hexdigest(),
        "secret_exposed": False,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(), ensure_ascii=False, indent=2))
