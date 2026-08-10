#!/usr/bin/env python3
"""Secret-safe live provider smoke through an already running Research OS service.

This script verifies the installed/local service from outside the service process:
health, provider credential visibility, live generation, and hosted web search when
an OpenAI Responses credential is configured. It never prints prompts, replies,
credential values, or provider error bodies.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


_DEFAULT_BASE_URL = "http://127.0.0.1:8787"
_REAL_PROVIDER_ORDER = ("openai-responses", "gemini", "anthropic")


def _request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 75.0,
) -> tuple[int, dict[str, Any]]:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(body) if body else {}
            return int(response.status), parsed if isinstance(parsed, dict) else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}
        return int(exc.code), parsed if isinstance(parsed, dict) else {}


def _error_code(payload: dict[str, Any]) -> str | None:
    raw = payload.get("error")
    if isinstance(raw, dict):
        value = raw.get("code")
        return str(value) if value else None
    if isinstance(raw, str):
        return raw
    return None


def _configured_providers(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = payload.get("providers")
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for name, value in raw.items():
        if isinstance(value, dict):
            result[str(name)] = value
    return result


def _select_real_provider(providers: dict[str, dict[str, Any]]) -> str | None:
    for name in _REAL_PROVIDER_ORDER:
        status = providers.get(name) or {}
        if bool(status.get("configured")) and not bool(status.get("secret_exposed")):
            return name
    return None


def run(base_url: str | None = None) -> tuple[int, dict[str, Any]]:
    base = (base_url or os.getenv("RESEARCH_OS_SMOKE_BASE_URL") or _DEFAULT_BASE_URL).strip()
    report: dict[str, Any] = {
        "service_url": base,
        "health_ok": False,
        "credential_status_ok": False,
        "real_provider_configured": False,
        "selected_provider": None,
        "generate_attempted": False,
        "generate_connected": False,
        "generate_response_received": False,
        "web_search_supported": False,
        "web_search_attempted": False,
        "web_search_connected": False,
        "web_search_response_received": False,
        "web_search_sources_received": False,
        "secret_safe": True,
    }

    try:
        health_status, health = _request_json(base, "/health", timeout=10.0)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        report["failure_stage"] = "health"
        return 3, report
    report["health_ok"] = health_status == 200 and health.get("status") == "ok"
    if not report["health_ok"]:
        report["failure_stage"] = "health"
        report["http_status"] = health_status
        return 3, report

    status_code, provider_payload = _request_json(base, "/v2/brain/providers", timeout=10.0)
    providers = _configured_providers(provider_payload)
    report["credential_status_ok"] = status_code == 200 and bool(providers)
    if not report["credential_status_ok"]:
        report["failure_stage"] = "credential_status"
        report["http_status"] = status_code
        report["error_code"] = _error_code(provider_payload)
        return 3, report

    selected = _select_real_provider(providers)
    report["selected_provider"] = selected
    report["real_provider_configured"] = selected is not None
    report["web_search_supported"] = bool(
        (providers.get("openai-responses") or {}).get("configured")
        and (providers.get("openai-responses") or {}).get("supports_web_search")
    )
    if selected is None:
        report["failure_stage"] = "real_provider_not_configured"
        return 2, report

    report["generate_attempted"] = True
    generate_status, generated = _request_json(
        base,
        "/v1/ai/generate",
        method="POST",
        payload={
            "provider": selected,
            "prompt": "Reply with exactly READY.",
            "system": "Connectivity smoke test. Do not include secrets or extra text.",
        },
    )
    report["generate_connected"] = generate_status == 200
    report["generate_response_received"] = bool(
        generate_status == 200 and str(generated.get("text") or "").strip()
    )
    if not report["generate_response_received"]:
        report["failure_stage"] = "generate"
        report["http_status"] = generate_status
        report["error_code"] = _error_code(generated)
        return 1, report

    if report["web_search_supported"]:
        report["web_search_attempted"] = True
        search_status, searched = _request_json(
            base,
            "/v2/brain/search",
            method="POST",
            payload={
                "provider": "openai-responses",
                "query": "Find the official OpenAI homepage and return a brief sourced confirmation.",
                "complexity_level": 1,
                "budget_workers": 1,
                "ready_workers": 1,
            },
        )
        result = searched.get("result") if isinstance(searched.get("result"), dict) else {}
        sources = result.get("sources") if isinstance(result, dict) else None
        report["web_search_connected"] = search_status == 200
        report["web_search_response_received"] = bool(
            search_status == 200 and str(result.get("text") or "").strip()
        )
        report["web_search_sources_received"] = bool(isinstance(sources, list) and sources)
        if not report["web_search_response_received"]:
            report["failure_stage"] = "web_search"
            report["http_status"] = search_status
            report["error_code"] = _error_code(searched)
            return 1, report

    report["passed"] = True
    return 0, report


def main() -> int:
    code, report = run()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
