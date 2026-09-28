#!/usr/bin/env python3
"""Validate the Platform self-reconciliation contract and safety boundary."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_PLATFORM_SELF_RECONCILIATION_CONTRACT.json"
ENGINE = ROOT / "tools" / "platform_self_reconciliation.py"

REQUIRED = (
    "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
    "current/PLANE_BOUNDARY_CONTRACT.json",
    "current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json",
    "current/ARCHITECTURE_INVARIANTS.md",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
    "tools/repair_diff_pipeline.py",
    "tools/platform_change_impact.py",
    "tools/platform_discovery.py",
    "tools/platform_graph.py",
)

def fail(message: str) -> None:
    print(f"PLATFORM_SELF_RECONCILIATION=FAIL: {message}")
    raise SystemExit(1)

def main() -> int:
    if not CONTRACT.is_file() or not ENGINE.is_file():
        fail("self-reconciliation contract or engine is missing")
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if data.get("status") != "ACTIVE":
        fail("contract is not ACTIVE")
    if data.get("release_authority") != "FINAL_GATE":
        fail("release authority drifted")
    if data.get("authority", {}).get("may_merge") is not False:
        fail("self-reconciliation must not merge")
    if data.get("authority", {}).get("may_modify_protected_core") is not False:
        fail("protected core mutation must remain forbidden")
    safety = data.get("safety", {})
    for key in (
        "exact_unique_target_required",
        "minimal_text_replacement_only",
        "ambiguous_target_stops",
        "protected_target_stops",
        "sandbox_before_apply",
        "snapshot_before_apply",
        "recon_after_apply_required",
        "rollback_required",
        "main_direct_write_forbidden",
        "auto_merge_forbidden",
        "unknown_is_not_pass",
    ):
        if safety.get(key) is not True:
            fail(f"safety rule missing: {key}")
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        fail("canonical anchors missing: " + ", ".join(missing))
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "tools.test_platform_self_reconciliation", "-v"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if tests.returncode != 0:
        fail("self-reconciliation tests failed: " + (tests.stdout or tests.stderr).strip())
    print("PLATFORM_SELF_RECONCILIATION=PASS")
    print("AUTO_REPAIR=DETERMINISTIC_ONLY")
    print("PROTECTED_CORE=FAIL_CLOSED")
    print("MAIN_DIRECT_WRITE=FORBIDDEN")
    print("POST_RECON=REQUIRED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
