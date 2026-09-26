#!/usr/bin/env python3
"""Validate the Research OS Laravel Platform boundary without requiring PHP."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "research_os_laravel"
CONTRACT = ROOT / "current" / "RESEARCH_OS_LARAVEL_PLATFORM_CONTRACT.json"


def main() -> int:
    required = [
        APP / "composer.json",
        APP / "artisan",
        APP / "bootstrap" / "app.php",
        APP / "routes" / "api.php",
        APP / "src" / "Platform" / "Contracts" / "AuthorizationGateway.php",
        APP / "src" / "Platform" / "Contracts" / "WorkflowGateway.php",
        APP / "tests" / "Unit" / "PlatformBoundaryTest.php",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    if missing:
        raise SystemExit(f"LARAVEL_PLATFORM_MISSING={missing}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    delivery = contract["delivery"]
    assert delivery["direct_engine_to_runner"] is False
    assert delivery["idempotency_required"] is True
    assert delivery["resource_conflict_fail_closed"] is True

    composer = json.loads((APP / "composer.json").read_text(encoding="utf-8"))
    assert composer["require"]["php"] == "^8.3"
    assert composer["require"]["laravel/framework"] == "^13.0"

    source = "\n".join(
        p.read_text(encoding="utf-8")
        for p in APP.rglob("*.php")
    )
    forbidden = ("Engine->Runner", "EngineToRunner", "directEngineToRunner")
    violations = [token for token in forbidden if token in source]
    if violations:
        raise SystemExit(f"LARAVEL_PLATFORM_DIRECT_EXECUTION_VIOLATION={violations}")

    print("RESEARCH_OS_LARAVEL_PLATFORM_BOUNDARY=PASS")
    print("RESEARCH_OS_LARAVEL_PLATFORM_FAIL_CLOSED=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
