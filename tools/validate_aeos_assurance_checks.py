"""Fail-closed validator for the AEOS assurance check universe.

This tool validates the *assurance mechanism* rather than inventing evidence.
A check can reach PASS only when its report entry is explicit, fresh,
independently verified, and backed by non-empty evidence references.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "current" / "AEOS_ASSURANCE_CHECK_REGISTRY.json"
ALLOWED = {"PASS", "FAIL", "UNKNOWN", "STALE", "CONFLICT", "BLOCKED", "QUARANTINED", "SELF_ATTESTED", "REVOKED", "EXPIRED"}
FORBIDDEN_PASS = {"UNKNOWN", "STALE", "CONFLICT", "BLOCKED", "QUARANTINED", "SELF_ATTESTED", "REVOKED", "EXPIRED"}


class AssuranceCheckError(ValueError):
    pass


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_sha(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise AssuranceCheckError(f"{label} must be an exact lowercase commit SHA")


def validate_registry() -> dict[str, Any]:
    data = _load(REGISTRY)
    if data.get("schema") != "research-os-aeos-assurance-check-registry/v1":
        raise AssuranceCheckError("unexpected assurance registry schema")
    if data.get("policy") != "fail_closed":
        raise AssuranceCheckError("assurance registry must be fail_closed")
    baseline = data.get("baseline_sha")
    _validate_sha(baseline, "registry baseline_sha")
    checks = data.get("checks")
    if type(checks) is not list or not checks:
        raise AssuranceCheckError("assurance registry must contain checks")
    ids: list[str] = []
    missing_boundaries: list[str] = []
    for item in checks:
        if type(item) is not dict:
            raise AssuranceCheckError("every check entry must be an object")
        check_id = item.get("id")
        check_class = item.get("class")
        if not isinstance(check_id, str) or not check_id.strip():
            raise AssuranceCheckError("check id is required")
        if check_id in ids:
            raise AssuranceCheckError(f"duplicate check id: {check_id}")
        ids.append(check_id)
        if not isinstance(check_class, str) or not check_class.strip():
            raise AssuranceCheckError(f"check class missing: {check_id}")
        boundary = item.get("boundary")
        if boundary is not None:
            path = ROOT / boundary
            if not path.is_file():
                missing_boundaries.append(f"{check_id}:{boundary}")
    if missing_boundaries:
        raise AssuranceCheckError("missing assurance boundaries: " + ", ".join(missing_boundaries))
    return {"check_count": len(checks), "registry_sha256": _sha256_json(data), "baseline_sha": baseline}


def validate_report(report: Mapping[str, Any], registry: Mapping[str, Any], expected_sha: str | None = None) -> dict[str, Any]:
    if report.get("baseline_sha") != registry.get("baseline_sha"):
        raise AssuranceCheckError("report baseline does not match registry baseline")
    report_head = report.get("observed_sha")
    _validate_sha(report_head, "report observed_sha")
    if expected_sha is not None:
        _validate_sha(expected_sha, "expected_sha")
        if report_head != expected_sha:
            raise AssuranceCheckError("report observed_sha does not match expected exact head SHA")
    checks = report.get("checks")
    if type(checks) is not dict:
        raise AssuranceCheckError("report checks must be a mapping")
    required = [item["id"] for item in registry["checks"]]
    if set(checks) != set(required):
        missing = sorted(set(required) - set(checks))
        extra = sorted(set(checks) - set(required))
        raise AssuranceCheckError(f"report check universe mismatch; missing={missing}; extra={extra}")
    failures: list[str] = []
    for check_id in required:
        entry = checks[check_id]
        if type(entry) is not dict:
            raise AssuranceCheckError(f"invalid report entry: {check_id}")
        status = entry.get("status")
        if status not in ALLOWED:
            raise AssuranceCheckError(f"invalid status for {check_id}: {status!r}")
        refs = entry.get("evidence_refs")
        if type(refs) is not list or not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise AssuranceCheckError(f"evidence required for {check_id}")
        independent = entry.get("independent")
        fresh = entry.get("fresh")
        if status == "PASS":
            if type(independent) is not bool or independent is not True:
                failures.append(f"{check_id}:PASS without independent=true")
            if type(fresh) is not bool or fresh is not True:
                failures.append(f"{check_id}:PASS without fresh=true")
            if entry.get("self_attested") is True:
                failures.append(f"{check_id}:self-attested PASS")
        if status in FORBIDDEN_PASS:
            failures.append(f"{check_id}:{status}")
    if failures:
        raise AssuranceCheckError("assurance report is not certifiable: " + ", ".join(failures))
    return {"report_status": "PASS", "check_count": len(required), "report_digest": _sha256_json(report)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    parser.add_argument("--registry-only", action="store_true")
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    registry_summary = validate_registry()
    if args.registry_only:
        if args.expected_sha is not None:
            _validate_sha(args.expected_sha, "expected_sha")
            actual = _git_head()
            if actual != args.expected_sha:
                raise AssuranceCheckError("working tree HEAD does not match expected exact head SHA")
        print(json.dumps({"registry": registry_summary, "status": "PASS"}, sort_keys=True))
        return 0
    if args.report is None:
        raise AssuranceCheckError("--report is required unless --registry-only is used")
    report = _load(args.report)
    registry = _load(REGISTRY)
    report_summary = validate_report(report, registry, args.expected_sha)
    print(json.dumps({"registry": registry_summary, "report": report_summary, "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssuranceCheckError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        raise SystemExit(1)
