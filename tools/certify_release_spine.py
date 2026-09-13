#!/usr/bin/env python3
"""Final certification gate: only a complete invariant set can produce PASS."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = ["SOURCE", "QUALITY", "BUILD", "IDENTITY", "PACKAGE", "INSTALL_E2E", "PROVENANCE", "LINEAGE", "CANDIDATE", "CERTIFICATION", "RELEASE"]
PROTECTED = {"TARGET_SHA", "OWNER_BUILD_IDENTITY", "SHA256", "INSTALLED_PROVENANCE", "CANONICAL_LINEAGE", "RELEASE_CERTIFICATION"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", default="current/GOLDEN_RELEASE_CONTRACT.yml")
    p.add_argument("--evidence", required=True)
    p.add_argument("--target-sha", required=True)
    p.add_argument("--output", default="reports/RELEASE_CERTIFICATION.json")
    args = p.parse_args()
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    errors: list[str] = []
    if evidence.get("immutable") is not True:
        errors.append("evidence must be immutable")
    if str(evidence.get("commit", "")).lower() != args.target_sha.strip().lower():
        errors.append("evidence commit does not match TARGET_SHA")
    if not str(evidence.get("run_id", "")).strip():
        errors.append("workflow run id is missing")
    gates = evidence.get("gates", {})
    for gate in REQUIRED[:-2]:
        if gates.get(gate) is not True:
            errors.append(f"release spine invariant failed: {gate}")
    if gates.get("CERTIFICATION") is True:
        errors.append("input evidence cannot self-assert CERTIFICATION")
    if gates.get("RELEASE") is True:
        errors.append("input evidence cannot self-assert RELEASE")
    protected = evidence.get("protected_gates", {})
    for name in sorted(PROTECTED - {"RELEASE_CERTIFICATION"}):
        if protected.get(name) is not True:
            errors.append(f"protected gate not proven: {name}")
    manifest_hash = evidence.get("manifest_sha256")
    if not isinstance(manifest_hash, str) or len(manifest_hash) != 64:
        errors.append("immutable evidence manifest_sha256 missing or malformed")
    else:
        copy = dict(evidence)
        copy.pop("manifest_sha256", None)
        payload = json.dumps(copy, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(payload).hexdigest() != manifest_hash:
            errors.append("immutable evidence manifest hash mismatch")
    contract = Path(args.contract)
    if not contract.is_file():
        errors.append("golden release contract missing")
    else:
        text = contract.read_text(encoding="utf-8")
        for item in REQUIRED:
            if f"  - {item}" not in text:
                errors.append(f"golden contract missing spine stage: {item}")
    result = {"version": 1, "certified": not errors, "status": "PASS" if not errors else "FAIL", "target_sha": args.target_sha.strip().lower(), "workflow_run_id": evidence.get("run_id"), "errors": errors, "auto_heal_is_trust": False}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
