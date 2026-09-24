#!/usr/bin/env python3
"""Validate the canonical cross-workflow platform contract."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "current" / "CANONICAL_PLATFORM_CONTRACT.yml"

REQUIRED_TOP_LEVEL = {
    "version", "name", "identity", "versioning", "state_machine",
    "resource_conflict", "retry", "reconciliation", "evidence",
    "provenance", "observability", "compatibility", "recovery",
    "fail_closed", "authority",
}


def load_contract(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("contract root must be a mapping")
    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        raise ValueError(f"missing top-level sections: {', '.join(missing)}")
    return data


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    identity = data["identity"]
    if identity["source_sha"].get("head_must_match") is not True:
        errors.append("source_sha.head_must_match must be true")
    if identity["source_sha"].get("mutation_invalidates_proof") is not True:
        errors.append("source_sha.mutation_invalidates_proof must be true")
    if identity["event"].get("immutable") is not True:
        errors.append("event must be immutable")
    if identity["idempotency"].get("required") is not True:
        errors.append("idempotency is required")

    state = data["state_machine"]
    if state.get("unknown_transition") != "STOP":
        errors.append("unknown transitions must STOP")
    if state.get("terminal_state_must_not_restart") is not True:
        errors.append("terminal states must not restart")

    conflict = data["resource_conflict"]
    if conflict.get("conflict_policy") != "REJECT":
        errors.append("resource conflicts must REJECT")
    for key in ("stop_execution", "release_resources", "ack_or_reconcile_delivery"):
        if conflict["on_reject"].get(key) is not True:
            errors.append(f"resource conflict on_reject.{key} must be true")
    if conflict.get("same_version_overwrite") is not False:
        errors.append("same-version overwrite must be false")

    retry = data["retry"]
    for key in ("bounded", "retry_must_preserve_failure_meaning",
                "retry_must_rebind_evidence", "retry_must_use_same_canonical_identity"):
        if retry.get(key) is not True:
            errors.append(f"retry.{key} must be true")

    evidence = data["evidence"]
    if evidence.get("immutable") is not True:
        errors.append("evidence must be immutable")
    required = set(evidence.get("required_fields", []))
    for field in ("event_id", "correlation_id", "source_sha", "target_sha",
                  "workflow_run_id", "contract_version", "fingerprint"):
        if field not in required:
            errors.append(f"evidence.required_fields missing {field}")

    provenance = data["provenance"]
    for key in ("exact_object_binding", "exact_execution_context_binding",
                "sha256_binding", "verifier_must_be_independent",
                "self_attestation_is_not_proof"):
        if provenance.get(key) is not True:
            errors.append(f"provenance.{key} must be true")

    if data["observability"].get("missing_trace") != "STOP":
        errors.append("missing observability trace must STOP")
    if data["compatibility"].get("unknown_contract_version") != "STOP":
        errors.append("unknown contract version must STOP")
    if data["recovery"].get("every_certified_main_requires_recovery_point") is not True:
        errors.append("certified main requires a recovery point")
    if data["authority"].get("final_gate_is_release_authority") is not True:
        errors.append("Final Gate must remain release authority")
    if data["authority"].get("contract_does_not_grant_merge_authority") is not True:
        errors.append("contract must not grant merge authority")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    path = Path(args.contract)
    try:
        data = load_contract(path)
        errors = validate(data)
    except Exception as exc:
        print(f"CANONICAL_PLATFORM_CONTRACT=FAIL: {exc}")
        return 1
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"CANONICAL_PLATFORM_CONTRACT=PASS: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
