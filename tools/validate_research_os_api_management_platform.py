#!/usr/bin/env python3
"""Validate the canonical API Management Platform management plane."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "tools/research_os_api/api_management_models.py",
    "tools/research_os_api/api_key_store.py",
    "tools/research_os_api/api_keys.py",
    "tools/research_os_api/api_platform/API_PLATFORM_CONTRACT.yaml",
    "tools/research_os_api/api_platform/API_PLATFORM_CAPABILITY_MATRIX.yaml",
    "tools/research_os_api/api_platform/api_management_registry.py",
    "tools/research_os_api/api_platform/management_service.py",
    "tools/research_os_api/api_platform/management_http.py",
    "tools/research_os_api/api_platform/test_management_service.py",
    "tools/research_os_api/server.py",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
)

def fail(message: str) -> None:
    print("API_MANAGEMENT_PLATFORM=FAIL")
    print(message)
    raise SystemExit(1)

def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        fail("missing anchors: " + ", ".join(missing))

    contract = (ROOT / "tools/research_os_api/api_platform/API_PLATFORM_CONTRACT.yaml").read_text(encoding="utf-8")
    for marker in (
        "namespace: /platform/v1",
        "management_owns:",
        "runtime_owns:",
        "raw_api_key: never_persisted",
        "management_state_does_not_authorize_execution",
    ):
        if marker not in contract:
            fail("management contract boundary missing: " + marker)

    server = (ROOT / "tools/research_os_api/server.py").read_text(encoding="utf-8")
    for marker in (
        "ManagementHTTP",
        'path.startswith("/platform/v1")',
        "_management_http()",
    ):
        if marker not in server:
            fail("management HTTP is not bound to canonical server: " + marker)

    matrix = (ROOT / "tools/research_os_api/api_platform/API_PLATFORM_CAPABILITY_MATRIX.yaml").read_text(encoding="utf-8")
    forbidden_management_status = (
        "status: CONTRACT_ONLY",
        "status: MISSING",
    )
    for capability in ("organizations", "projects", "applications", "api_catalog", "api_versions",
                       "endpoints", "plans", "webhooks", "developer_portal", "sdk_metadata"):
        start = matrix.find(f"  {capability}:")
        if start < 0:
            fail("capability missing: " + capability)
        end = matrix.find("\n  ", start + 4)
        section = matrix[start:] if end < 0 else matrix[start:end]
        if any(status in section for status in forbidden_management_status):
            fail(f"capability remains unimplemented: {capability}")

    gate = (ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml").read_text(encoding="utf-8")
    if "api_management_platform:" not in gate:
        fail("API Management Platform is not bound to Unified Final Gate")

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "tools.research_os_api.api_platform.test_management_service", "-v"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if result.returncode != 0:
        fail("management service tests failed:\n" + (result.stdout or result.stderr)[-6000:])

    print("API_MANAGEMENT_PLATFORM=PASS")
    print("MANAGEMENT_METADATA=CANONICAL")
    print("API_KEY_PERSISTENCE=DURABLE_DIGEST_ONLY")
    print("API_KEY_ROTATION=BOUND")
    print("MANAGEMENT_HTTP=BOUND_TO_RESEARCH_OS_API")
    print("RUNTIME_AUTHORITY=RESOURCE_CONTROL_PLANE")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
