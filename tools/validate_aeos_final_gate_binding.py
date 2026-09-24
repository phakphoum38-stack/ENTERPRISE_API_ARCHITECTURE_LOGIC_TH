#!/usr/bin/env python3
"""Fail-closed validation of existing AEOS Master Assurance evidence for Final Gate.

This is a binding/reconciliation validator only. It does not create a new
assurance authority, ledger, or release authority.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_DECISIONS = {"FAIL", "INSUFFICIENT_EVIDENCE", "UNKNOWN", "STALE", "CONFLICT", "BLOCKED", "QUARANTINED", "SELF_ATTESTED", "REVOKED", "EXPIRED"}


def validate_manifest(path: Path, expected_sha: str) -> dict[str, object]:
    if not SHA_RE.fullmatch(expected_sha):
        raise ValueError("expected_sha must be an exact lowercase commit SHA")
    if not path.is_file():
        raise ValueError(f"missing AEOS evidence manifest: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "AEOS_MASTER_ASSURANCE_V2":
        raise ValueError("unsupported AEOS assurance manifest schema")
    if data.get("source_sha") != expected_sha:
        raise ValueError("AEOS evidence source SHA does not match Final Gate target SHA")
    if data.get("decision") != "PASS":
        raise ValueError(f"AEOS evidence is not admissible: {data.get('decision')!r}")
    if data.get("decision") in FORBIDDEN_DECISIONS:
        raise ValueError("AEOS evidence is in a forbidden non-pass state")
    controls = data.get("controls")
    if not isinstance(controls, list) or not controls:
        raise ValueError("AEOS evidence contains no controls")
    if data.get("control_count") != len(controls):
        raise ValueError("AEOS control_count does not match evidence")
    for control in controls:
        if not isinstance(control, dict):
            raise ValueError("invalid AEOS control record")
        if control.get("status") != "PASS":
            raise ValueError(f"AEOS control is not PASS: {control.get('control_id')}")
        if control.get("returncode") != 0:
            raise ValueError(f"AEOS PASS control has non-zero return code: {control.get('control_id')}")
        evidence_id = control.get("evidence_id")
        if not isinstance(evidence_id, str) or not re.fullmatch(r"[0-9a-f]{64}", evidence_id):
            raise ValueError(f"invalid evidence_id: {control.get('control_id')}")
    return {
        "binding": "PASS",
        "source_sha": expected_sha,
        "control_count": len(controls),
        "decision": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    result = validate_manifest(Path(args.manifest), args.expected_sha)
    print("AEOS_FINAL_GATE_BINDING=PASS")
    print(f"AEOS_SOURCE_SHA={result['source_sha']}")
    print(f"AEOS_CONTROL_COUNT={result['control_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
