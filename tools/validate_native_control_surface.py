#!/usr/bin/env python3
"""Fail-closed validator for the Native Control Surface contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_CAPABILITIES = {
    "COMMAND_DISCOVERY",
    "SEMANTIC_SEARCH",
    "UNIVERSAL_INSPECTOR",
    "SYSTEM_MAP",
    "OBJECT_TRACE",
    "WHY_TRACE",
}
REQUIRED_INVARIANTS = {
    "search_is_read_only",
    "inspection_is_read_only",
    "navigation_does_not_grant_authority",
    "command_preparation_is_not_execution",
    "unknown_is_preserved",
    "provenance_is_preserved",
    "evidence_is_not_authority",
    "human_authority_boundaries_are_preserved",
    "no_duplicate_control_center",
    "no_duplicate_runtime",
    "no_duplicate_memory",
    "no_duplicate_assurance",
    "no_history_rewrite",
    "10^1000_is_logical_only",
}


def validate(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("contract_id") != "research-os-native-control-surface-v1":
        raise ValueError("invalid contract_id")
    if data.get("status") != "ACTIVE":
        raise ValueError("contract must be ACTIVE")
    if not REQUIRED_CAPABILITIES.issubset(set(data.get("capabilities", []))):
        raise ValueError("required capabilities are missing")
    if not REQUIRED_INVARIANTS.issubset(set(data.get("invariants", []))):
        raise ValueError("required invariants are missing")
    authority = data.get("authority", {})
    for field in ("may_execute", "may_authorize", "may_approve", "may_release", "may_merge", "may_change_branch_protection", "may_rewrite_history"):
        if authority.get(field) is not False:
            raise ValueError(f"authority boundary not fail-closed: {field}")
    bounds = data.get("bounds", {})
    for field in ("max_search_results", "max_inspector_relations", "max_inspector_evidence", "max_trace_depth", "max_activity_items"):
        if not isinstance(bounds.get(field), int) or bounds[field] < 1:
            raise ValueError(f"invalid bound: {field}")
    return {
        "status": "PASS",
        "contract_id": data["contract_id"],
        "contract_sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="current/NATIVE_CONTROL_SURFACE_CONTRACT.json")
    args = parser.parse_args()
    try:
        result = validate(Path(args.contract))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
