#!/usr/bin/env python3
"""Fail-closed validator for the reusable Platform operationalization contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/PLATFORM_OPERATIONALIZATION_CONTRACT.json"
IMPLEMENTATION = ROOT / "tools/platform_operationalization.py"
TEST = ROOT / "tools/test_platform_operationalization.py"


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"PLATFORM_OPERATIONALIZATION=FAIL: {message}")


def main() -> None:
    for path in (CONTRACT, IMPLEMENTATION, TEST):
        if not path.is_file():
            fail(f"missing required anchor: {path.relative_to(ROOT)}")
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if data.get("status") != "ACTIVE":
        fail("contract is not ACTIVE")
    authority = data.get("authority", {})
    forbidden = ("may_execute", "may_authorize", "may_approve", "may_merge", "may_release")
    if any(authority.get(key) is not False for key in forbidden):
        fail("authority boundary permits a forbidden operation")
    if authority.get("release_authority") != "FINAL_GATE":
        fail("release authority drifted")
    continuity = data.get("continuity", {})
    if continuity.get("chat_is_not_source_of_truth") is not True:
        fail("chat source-of-truth boundary missing")
    if continuity.get("sha_mismatch") != "HOLD":
        fail("SHA mismatch must HOLD")
    if continuity.get("unknown") != "HOLD":
        fail("unknown must HOLD")
    guard = data.get("impact_guard", {})
    required = {"contracts", "workflows", "tests", "final_gate", "invariants", "product_surfaces"}
    if set(guard.get("checks", [])) != required:
        fail("impact guard categories drifted")
    if guard.get("missing_required_impact") != "HOLD":
        fail("missing impact must HOLD")
    if "no_runtime_mutation" not in data.get("rules", []):
        fail("runtime mutation boundary missing")
    print("PLATFORM_OPERATIONALIZATION=PASS")
    print("AUTHORITY=DESCRIPTIVE_VALIDATING")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    print("CONTINUITY=SOURCE_PINNED")
    print("IMPACT_GUARD=FAIL_CLOSED")


if __name__ == "__main__":
    main()
