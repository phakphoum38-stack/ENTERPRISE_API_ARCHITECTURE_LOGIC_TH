#!/usr/bin/env python3
"""Build tamper-evident evidence for a bounded Autobot repair diff."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VERIFICATION_STATUSES = {"NOT_RUN", "PASS", "FAIL", "UNKNOWN"}


def _require_sha(name: str, value: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise ValueError(f"{name} must be a 40-character commit SHA")
    return value


def build_evidence(
    *,
    diff: str,
    validation: dict[str, object],
    base_ref: str,
    base_sha: str,
    head_ref: str,
    head_sha: str,
    applied: bool = False,
    verification_status: str = "NOT_RUN",
    verification_ref: str | None = None,
    repair_id: str | None = None,
) -> dict[str, object]:
    """Create canonical evidence and reject metadata that does not bind to diff."""
    if not isinstance(validation, dict):
        raise ValueError("validation must be an object")
    expected_hash = hashlib.sha256(diff.encode("utf-8")).hexdigest()
    if validation.get("status") not in {"PASS", "FAIL"}:
        raise ValueError("validation status must be PASS or FAIL")
    if validation.get("sha256") != expected_hash:
        raise ValueError("validation SHA-256 does not match repair diff")
    if validation.get("bytes") != len(diff.encode("utf-8")):
        raise ValueError("validation byte count does not match repair diff")
    files = validation.get("files")
    if not isinstance(files, list) or validation.get("file_count") != len(files):
        raise ValueError("validation file metadata is inconsistent")
    if validation.get("apply_to_main") is not False:
        raise ValueError("validation must keep apply_to_main=false")
    if validation.get("auto_merge") is not False:
        raise ValueError("validation must keep auto_merge=false")
    if verification_status not in VERIFICATION_STATUSES:
        raise ValueError(f"unsupported verification status: {verification_status}")
    if verification_status == "NOT_RUN" and verification_ref:
        raise ValueError("verification_ref requires a verification status other than NOT_RUN")

    return {
        "schema": "autobot-repair-diff-evidence/v1",
        "repair_id": repair_id,
        "diff": {
            "sha256": expected_hash,
            "bytes": len(diff.encode("utf-8")),
            "files": list(files),
            "file_count": validation["file_count"],
            "hunk_count": validation["hunk_count"],
        },
        "lineage": {
            "base_ref": base_ref,
            "base_sha": _require_sha("base_sha", base_sha),
            "head_ref": head_ref,
            "head_sha": _require_sha("head_sha", head_sha),
        },
        "validation": {
            "status": validation["status"],
            "errors": list(validation["errors"]),
        },
        "application": {
            "applied": bool(applied),
            "target": "task-branch",
            "apply_to_main": False,
            "auto_merge": False,
        },
        "verification": {
            "status": verification_status,
            "ref": verification_ref,
        },
    }


def write_evidence(path: Path, evidence: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", required=True, help="repair diff to bind to evidence")
    parser.add_argument("--validation", required=True, help="validation JSON produced by repair_diff_pipeline")
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repair-id")
    parser.add_argument("--applied", action="store_true")
    parser.add_argument("--verification-status", choices=sorted(VERIFICATION_STATUSES), default="NOT_RUN")
    parser.add_argument("--verification-ref")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    diff = Path(args.diff).read_text(encoding="utf-8")
    validation = json.loads(Path(args.validation).read_text(encoding="utf-8"))
    evidence = build_evidence(
        diff=diff,
        validation=validation,
        base_ref=args.base_ref,
        base_sha=args.base_sha,
        head_ref=args.head_ref,
        head_sha=args.head_sha,
        applied=args.applied,
        verification_status=args.verification_status,
        verification_ref=args.verification_ref,
        repair_id=args.repair_id,
    )
    write_evidence(Path(args.output), evidence)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
