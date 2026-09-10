#!/usr/bin/env python3
"""Validate AEOS assurance manifests and their cryptographic sidecar evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SCHEMA = "AEOS_MASTER_ASSURANCE_V2"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"PASS", "FAIL"}
DECISIONS = {"PASS", "FAIL", "INSUFFICIENT_EVIDENCE"}
FAILURE_STATUSES = {"FAIL", "ERROR", "STALE", "INSUFFICIENT_EVIDENCE"}


def _die(reason: str) -> None:
    raise SystemExit(reason)


def _load(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _die(f"invalid_manifest:{type(exc).__name__}")
    if not isinstance(data, dict):
        _die("invalid_manifest:object_required")
    return data


def _git_commit_exists(sha: str, repo: Path) -> bool:
    if not SHA_RE.fullmatch(sha):
        return False
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _verify_sidecar(manifest: Path) -> str:
    sidecar = Path(str(manifest) + ".sha256")
    if not sidecar.is_file():
        _die(f"missing_manifest_digest:{sidecar}")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    matches = False
    for line in sidecar.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1].lstrip("*") == manifest.name and fields[0] == digest:
            matches = True
            break
    if not matches:
        _die(f"manifest_digest_mismatch:{manifest}")
    return digest


def _validate_control(item: object) -> None:
    if not isinstance(item, dict):
        _die("invalid_control_record")
    required = ("control_id", "class_name", "status", "command", "cwd", "returncode", "duration_seconds", "evidence_id")
    missing = [key for key in required if key not in item]
    if missing:
        _die(f"missing_control_fields:{missing}")
    if not isinstance(item["control_id"], str) or not item["control_id"]:
        _die("invalid_control_id")
    if item["status"] not in STATUSES:
        _die(f"invalid_control_status:{item['control_id']}")
    if not isinstance(item["command"], list) or not item["command"] or not all(isinstance(v, str) for v in item["command"]):
        _die(f"invalid_control_command:{item['control_id']}")
    if not isinstance(item["cwd"], str):
        _die(f"invalid_control_cwd:{item['control_id']}")
    if not isinstance(item["returncode"], int):
        _die(f"invalid_control_returncode:{item['control_id']}")
    if not isinstance(item["evidence_id"], str) or not DIGEST_RE.fullmatch(item["evidence_id"]):
        _die(f"invalid_evidence_id:{item['control_id']}")
    if item["status"] == "PASS" and item["returncode"] != 0:
        _die(f"pass_returncode_mismatch:{item['control_id']}")
    if item["status"] != "PASS":
        signature = item.get("failure_signature")
        if not isinstance(signature, str) or not signature:
            _die(f"missing_failure_signature:{item['control_id']}")
        if item["returncode"] == 0:
            _die(f"failure_returncode_mismatch:{item['control_id']}")


def validate_manifest(path: Path, *, repo: Path, require_commit: bool) -> str:
    if not path.is_file():
        _die(f"missing_manifest:{path}")
    data = _load(path)
    if data.get("schema") != SCHEMA:
        _die(f"unsupported_manifest_schema:{data.get('schema')}")
    source_sha = data.get("source_sha")
    if not isinstance(source_sha, str) or not SHA_RE.fullmatch(source_sha):
        _die("invalid_source_sha")
    if require_commit and not _git_commit_exists(source_sha, repo):
        _die(f"unknown_source_sha:{source_sha}")
    controls = data.get("controls")
    if not isinstance(controls, list) or not controls:
        _die("invalid_controls")
    if data.get("control_count") != len(controls):
        _die("control_count_mismatch")
    ids = []
    for item in controls:
        _validate_control(item)
        assert isinstance(item, dict)
        ids.append(item["control_id"])
    if len(ids) != len(set(ids)):
        _die("duplicate_control_id")
    passed = data.get("passed")
    failed = data.get("failed")
    if not isinstance(passed, int) or not isinstance(failed, int):
        _die("invalid_result_counts")
    actual_failed = sum(item.get("status") != "PASS" for item in controls if isinstance(item, dict))
    actual_passed = len(controls) - actual_failed
    if (passed, failed) != (actual_passed, actual_failed):
        _die(f"result_count_mismatch:{passed}:{failed}:{actual_passed}:{actual_failed}")
    decision = data.get("decision")
    if decision not in DECISIONS:
        _die(f"invalid_decision:{decision}")
    fix = data.get("fix_verification")
    if not isinstance(fix, dict) or fix.get("status") not in {"NOT_REQUESTED", "PASS", "FAIL", "INSUFFICIENT_EVIDENCE"}:
        _die("invalid_fix_verification")
    expected = "FAIL" if failed else "PASS"
    if fix["status"] == "FAIL":
        expected = "FAIL"
    elif fix["status"] == "INSUFFICIENT_EVIDENCE":
        expected = "INSUFFICIENT_EVIDENCE"
    if decision != expected:
        _die(f"decision_mismatch:{decision}:{expected}")
    if fix["status"] != "NOT_REQUESTED":
        old_sha = fix.get("old_sha")
        new_sha = fix.get("new_sha")
        if not isinstance(old_sha, str) or not SHA_RE.fullmatch(old_sha):
            _die("invalid_fix_old_sha")
        if not isinstance(new_sha, str) or not SHA_RE.fullmatch(new_sha):
            _die("invalid_fix_new_sha")
        if old_sha == new_sha:
            _die("fix_sha_not_changed")
        if require_commit and not _git_commit_exists(old_sha, repo):
            _die(f"unknown_fix_old_sha:{old_sha}")
        if new_sha != source_sha:
            _die("fix_new_sha_not_bound_to_manifest")
        for key in ("regressions", "resolved_failures"):
            if not isinstance(fix.get(key), list) or not all(isinstance(v, str) for v in fix[key]):
                _die(f"invalid_fix_list:{key}")
        if fix["status"] == "PASS" and fix["regressions"]:
            _die("fix_pass_with_regressions")
    return _verify_sidecar(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--previous", action="store_true", help="Validate as prior evidence; require a resolvable historical commit")
    args = parser.parse_args()
    digest = validate_manifest(Path(args.manifest), repo=Path(args.repo).resolve(), require_commit=True)
    print(f"MANIFEST_SCHEMA={SCHEMA}")
    print("MANIFEST_SEMANTICS=PASS")
    print("MANIFEST_PROVENANCE_DIGEST=PASS")
    print(f"MANIFEST_SHA256={digest}")
    if args.previous:
        print("PREVIOUS_MANIFEST_PROVENANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
