#!/usr/bin/env python3
"""AEOS Master Assurance orchestrator.

Runs independent assurance controls in one invocation while preserving per-control
failure isolation and producing one machine-readable assurance manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURE_STATUSES = {"FAIL", "ERROR", "STALE", "INSUFFICIENT_EVIDENCE"}
MANIFEST_SCHEMA = "AEOS_MASTER_ASSURANCE_V2"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass
class ControlResult:
    control_id: str
    class_name: str
    status: str
    command: list[str]
    cwd: str
    returncode: int
    duration_seconds: float
    detail: str = ""
    evidence_id: str = ""
    failure_signature: str | None = None


def _normalize_failure_detail(detail: str) -> str:
    """Remove volatile execution metadata while preserving failure semantics."""
    normalized = " ".join(detail.split())
    normalized = re.sub(r"\baeos-[0-9]+-[0-9]+\b", "<run-id>", normalized)
    normalized = re.sub(r"\b[0-9a-f]{40}\b", "<sha>", normalized)
    normalized = re.sub(r"\b[0-9a-f]{64}\b", "<digest>", normalized)
    normalized = re.sub(r"\b(?:duration|elapsed|time)[=:][0-9.]+s?\b", r"\1=<time>", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(?<!\w)(?:line|lineno)[=:][0-9]+", "line=<number>", normalized, flags=re.IGNORECASE)
    return normalized


def failure_signature(control_id: str, class_name: str, command: list[str], detail: str) -> str:
    """Create a stable recurrence identity independent of volatile run metadata."""
    command_identity = " ".join(command)
    semantic_detail = _normalize_failure_detail(detail)
    payload = "|".join((control_id, class_name, command_identity, semantic_detail))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{control_id}:{digest}"


def failure_event_id(control_id: str, returncode: int, detail: str) -> str:
    """Create an exact evidence identity for this particular failure event."""
    payload = f"{control_id}|{returncode}|{detail}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_control(
    control_id: str,
    class_name: str,
    command: list[str],
    control_cwd: Path | None = None,
) -> ControlResult:
    started = time.monotonic()
    cwd = control_cwd or ROOT
    env = None
    if control_id == "V3_REGRESSION":
        # V3 tests intentionally use both import forms: v3.<module> and
        # research_os_v3.<module>. Running with cwd=v3 supplies the latter,
        # but removes the repository root from sys.path and breaks the former.
        # Bind both roots explicitly in the subprocess instead of changing tests.
        env = os.environ.copy()
        pythonpath = [str(ROOT), str(cwd)]
        existing = env.get("PYTHONPATH", "").strip()
        if existing:
            pythonpath.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
        )
        returncode = proc.returncode
        output = (proc.stdout + "\n" + proc.stderr).strip()
    except Exception as exc:  # fail closed: a control that cannot execute is not PASS
        returncode = 125
        output = f"control_execution_error:{type(exc).__name__}:{exc}"
    duration = round(time.monotonic() - started, 3)
    detail = output[-4000:] if output else ""
    status = "PASS" if returncode == 0 else "FAIL"
    evidence_id = failure_event_id(control_id, returncode, detail)
    return ControlResult(
        control_id=control_id,
        class_name=class_name,
        status=status,
        command=command,
        cwd=str(cwd.relative_to(ROOT)),
        returncode=returncode,
        duration_seconds=duration,
        detail=detail,
        evidence_id=evidence_id,
        failure_signature=(failure_signature(control_id, class_name, command, detail) if status != "PASS" else None),
    )


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def git_base_sha() -> str:
    return os.environ.get("AEOS_BASE_SHA", "").strip()


def git_sha_exists(sha: str) -> bool:
    if not SHA_RE.fullmatch(sha):
        return False
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_scope(base_sha: str, source_sha: str) -> dict[str, object]:
    if not base_sha:
        return {"status": "NOT_REQUESTED", "base_sha": None, "changed_files": []}
    try:
        names = subprocess.check_output(
            ["git", "diff", "--name-only", base_sha, source_sha],
            cwd=ROOT,
            text=True,
        ).splitlines()
        return {
            "status": "PASS",
            "base_sha": base_sha,
            "source_sha": source_sha,
            "changed_files": names,
            "changed_file_count": len(names),
        }
    except subprocess.CalledProcessError as exc:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "base_sha": base_sha,
            "source_sha": source_sha,
            "changed_files": [],
            "error": f"scope_diff_error:{exc}",
        }


def _validate_previous_control(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    required = ("control_id", "class_name", "status", "command", "cwd", "returncode", "evidence_id")
    if any(key not in item for key in required):
        return False
    if not isinstance(item["control_id"], str) or not item["control_id"]:
        return False
    if not isinstance(item["class_name"], str) or not item["class_name"]:
        return False
    if item["status"] not in {"PASS", "FAIL"}:
        return False
    if not isinstance(item["command"], list) or not item["command"] or not all(isinstance(v, str) for v in item["command"]):
        return False
    if not isinstance(item["cwd"], str):
        return False
    if not isinstance(item["returncode"], int):
        return False
    if not isinstance(item["evidence_id"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["evidence_id"]):
        return False
    if item["status"] != "PASS" and not item.get("failure_signature"):
        return False
    return True


def load_previous_manifest(path: str) -> dict[str, object] | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.is_file():
        raise SystemExit(f"missing_previous_manifest:{path}")
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid_previous_manifest:{type(exc).__name__}") from exc
    if not isinstance(data, dict):
        raise SystemExit("invalid_previous_manifest:object_required")
    if data.get("schema") != MANIFEST_SCHEMA:
        raise SystemExit(f"invalid_previous_manifest:schema:{data.get('schema')}")
    old_sha = data.get("source_sha")
    if not isinstance(old_sha, str) or not SHA_RE.fullmatch(old_sha):
        raise SystemExit("invalid_previous_manifest:source_sha")
    if old_sha == git_sha():
        raise SystemExit("invalid_previous_manifest:source_sha_is_current")
    if not git_sha_exists(old_sha):
        raise SystemExit(f"invalid_previous_manifest:unknown_source_sha:{old_sha}")
    controls = data.get("controls")
    if not isinstance(controls, list) or not controls:
        raise SystemExit("invalid_previous_manifest:controls")
    if data.get("control_count") != len(controls):
        raise SystemExit("invalid_previous_manifest:control_count")
    if len({item.get("control_id") for item in controls if isinstance(item, dict)}) != len(controls):
        raise SystemExit("invalid_previous_manifest:duplicate_control_id")
    if any(not _validate_previous_control(item) for item in controls):
        raise SystemExit("invalid_previous_manifest:control_record")
    if data.get("decision") not in {"PASS", "FAIL", "INSUFFICIENT_EVIDENCE"}:
        raise SystemExit("invalid_previous_manifest:decision")
    passed = data.get("passed")
    failed = data.get("failed")
    if not isinstance(passed, int) or not isinstance(failed, int) or passed + failed != len(controls):
        raise SystemExit("invalid_previous_manifest:result_counts")
    return data


def verify_fix(current: list[ControlResult], previous: dict[str, object] | None) -> dict[str, object]:
    if previous is None:
        return {
            "status": "NOT_REQUESTED",
            "mode": "none",
            "old_sha": None,
            "new_sha": git_sha(),
            "regressions": [],
            "resolved_failures": [],
        }

    old_sha = str(previous["source_sha"])
    new_sha = git_sha()
    old_controls = previous["controls"]
    assert isinstance(old_controls, list)
    old_failures = {
        str(item["failure_signature"])
        for item in old_controls
        if isinstance(item, dict) and item.get("status") in FAILURE_STATUSES and item.get("failure_signature")
    }
    new_failures = {
        r.failure_signature for r in current if r.status in FAILURE_STATUSES and r.failure_signature
    }
    regressions = sorted(new_failures - old_failures)
    resolved = sorted(old_failures - new_failures)
    status = "PASS" if not regressions else "FAIL"
    return {
        "status": status,
        "mode": "previous_manifest",
        "old_sha": old_sha,
        "new_sha": new_sha,
        "old_decision": previous.get("decision"),
        "old_failure_signatures": sorted(old_failures),
        "current_failure_signatures": sorted(new_failures),
        "regressions": regressions,
        "resolved_failures": resolved,
    }


def discover_controls() -> list[tuple[str, str, list[str], Path]]:
    controls: list[tuple[str, str, list[str], Path]] = []

    expected = os.environ.get("AEOS_EXPECTED_SHA", "").strip()
    if expected:
        controls.append(
            (
                "IDENTITY_SHA",
                "identity",
                [sys.executable, "-c", f"import subprocess; actual=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); expected={expected!r}; print(actual); assert actual == expected, f'expected {{expected}}, got {{actual}}'"],
                ROOT,
            )
        )

    compile_paths = [p for p in (ROOT / "owner_special", ROOT / "tools") if p.exists()]
    if compile_paths:
        controls.append(
            (
                "PYTHON_COMPILE",
                "static",
                [sys.executable, "-m", "compileall", "-q", *(str(p.relative_to(ROOT)) for p in compile_paths)],
                ROOT,
            )
        )

    validator_candidates = [
        ROOT / "tools" / "validate_aeos_source_checks.py",
        ROOT / "tools" / "validate_aeos_assurance_checks.py",
        ROOT / "tools" / "validate_provenance_evidence.py",
    ]
    for path in validator_candidates:
        if path.is_file():
            args = [sys.executable, str(path.relative_to(ROOT))]
            if path.name == "validate_aeos_assurance_checks.py":
                args.append("--registry-only")
            controls.append((path.stem.upper(), "validator", args, ROOT))

    test_dir = ROOT / "owner_special" / "tests"
    if test_dir.is_dir():
        controls.append(
            (
                "AEOS_REGRESSION",
                "behavioral",
                [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir.relative_to(ROOT)), "-p", "test_aeos_*.py", "-v"],
                ROOT,
            )
        )

    v3_test_dir = ROOT / "v3" / "tests"
    v3_package_dir = ROOT / "v3"
    if v3_test_dir.is_dir() and (v3_package_dir / "research_os_v3").is_dir():
        # Keep the established V3 execution boundary: tests run from v3/ with
        # -s tests. run_control supplies both repository-root and v3 import roots
        # so tests importing v3.* and research_os_v3.* both resolve correctly.
        controls.append(
            (
                "V3_REGRESSION",
                "integration",
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
                v3_package_dir,
            )
        )

    return controls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="aeos_master_assurance_manifest.json")
    parser.add_argument("--previous-manifest", default="", help="Explicit prior assurance manifest for old-vs-new fix verification")
    args = parser.parse_args()

    controls = discover_controls()
    if not controls:
        print("AEOS_MASTER_ASSURANCE=FAIL: no executable controls discovered")
        return 2

    results: list[ControlResult] = []
    # Controls are independent: one failure must not cancel or suppress the others.
    with ThreadPoolExecutor(max_workers=len(controls)) as executor:
        futures = {
            executor.submit(run_control, control_id, class_name, command, control_cwd): control_id
            for control_id, class_name, command, control_cwd in controls
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    results.sort(key=lambda item: item.control_id)

    for result in results:
        print(f"[{result.status}] {result.control_id} ({result.duration_seconds}s)")
        if result.status != "PASS":
            print(result.detail)

    source_sha = git_sha()
    previous = load_previous_manifest(args.previous_manifest)
    failed = [r for r in results if r.status != "PASS"]
    fix_verification = verify_fix(results, previous)
    decision = "FAIL" if failed or fix_verification["status"] == "FAIL" else "PASS"
    if fix_verification["status"] == "INSUFFICIENT_EVIDENCE":
        decision = "INSUFFICIENT_EVIDENCE"

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "assurance_run_id": os.environ.get("AEOS_ASSURANCE_RUN_ID", f"local-{int(time.time())}"),
        "source_sha": source_sha,
        "base_sha": git_base_sha() or None,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "control_count": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "decision": decision,
        "decision_reasons": [
            "control_failure" if failed else "all_controls_pass",
            "fix_regression" if fix_verification["status"] == "FAIL" else "fix_verification_not_failed",
        ],
        "change_scope": git_scope(git_base_sha(), source_sha),
        "fix_verification": fix_verification,
        "controls": [asdict(r) for r in results],
    }
    output = ROOT / args.output
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("assurance_run_id", "source_sha", "control_count", "passed", "failed", "decision")}, indent=2))
    return 1 if decision != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
