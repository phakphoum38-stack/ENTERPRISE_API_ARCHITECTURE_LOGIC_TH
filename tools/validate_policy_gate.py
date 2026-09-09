#!/usr/bin/env python3
"""Validate P0-06 contract, fixture, compiler invariants, and deterministic output."""
from __future__ import annotations

import json
from pathlib import Path

from tools.compile_policy_gate import compile_policy

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "POLICY_GATE_CONTRACT.json"
FIXTURE = ROOT / "current" / "POLICY_GATE_FIXTURE.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors: list[str] = []

    if contract.get("contract_id") != "PGC-001":
        errors.append("invalid_contract_id")
    if contract.get("status") != "canonical":
        errors.append("contract_not_canonical")
    if contract.get("unknown_state") != "BLOCK":
        errors.append("unknown_state_not_block")
    if contract.get("enforcement", {}).get("fail_closed") is not True:
        errors.append("fail_closed_not_enabled")
    boundary = contract.get("authority_boundary", {})
    for key in ("may_grant_authority", "may_replace_owner_policy", "may_replace_approval_gate", "may_execute_runtime_action"):
        if boundary.get(key) is not False:
            errors.append(f"authority_boundary_violation:{key}")

    try:
        plan = compile_policy(fixture)
    except Exception as exc:
        errors.append(f"compile_failure:{exc}")
        plan = None

    if plan is not None:
        if plan.get("authority_effect") != "NONE":
            errors.append("compiler_has_authority_effect")
        if plan.get("policy_fingerprint") != fixture.get("policy_fingerprint"):
            errors.append("policy_fingerprint_mismatch")
        if not plan.get("gates"):
            errors.append("no_gates")

    print(json.dumps({"contract": str(CONTRACT.relative_to(ROOT)), "status": "PASS" if not errors else "FAIL", "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
