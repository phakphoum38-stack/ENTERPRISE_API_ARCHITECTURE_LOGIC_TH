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
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURE_STATUSES = {"FAIL", "ERROR", "STALE", "INSUFFICIENT_EVIDENCE"}


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


def failure_signature(control_id: str, detail: str) -> str:
    normalized = " ".join(detail.split())
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"{control_id}:{digest}"


def run_control(
    control_id: str,
    class_name: str,
    command: list[str],
    control_cwd: Path | None = None,
) -> ControlResult:
    started = time.monotonic()
    cwd = control_cwd or ROOT
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        returncode = proc.returncode
        output = (proc.stdout + "\n" + proc.stderr).strip()
    except Exception as exc:  # fail closed: a control that cannot execute is not PASS
        returncode = 125
        output = f"control_execution_error:{type(exc).__name__}:{exc}"
    duration = round(time.monotonic() - started, 3)
    detail = output[-4000:] if output else ""
    status = "PASS" if returncode == 0 else "FAIL"
    evidence_id = hashlib.sha256(
        f"{control_id}|{returncode}|{detail}".encode("utf-8")
    ).hexdigest()
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
        failure_signature=failure_signature(control_id, detail) if status != "PASS" else None,
    )


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def git_base_sha() -> str:
    return os.environ.get("AEOS_BASE_SHA", "").strip()


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


def load_previous_manifest(path: str) -> dict[str, object] | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.is_file():
        raise SystemExit(f"missing_previous_manifest:{path}")
    data = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "controls" not in data or "source_sha" not in data:
        raise SystemExit("invalid_previous_manifest")
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
    old_controls = previous.get("controls", [])
    if not isinstance(old_controls, list):
        return {"status": "INSUFFICIENT_EVIDENCE", "mode": "previous_manifest", "old_sha": old_sha, "new_sha": new_sha, "regressions": [], "resolved_failures": []}

    old_failures = {
        str(item.get("failure_signature"))
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
        # V3 tests use both import forms: v3.<module> and research_os_v3.<module>.
        # The repository root is required for the namespace package `v3`, while
        # v3/ itself is required for the package-local `research_os_v3` imports.
        # Keep the existing V3 tests unchanged and bind both source roots explicitly
        # inside the assurance subprocess.
        v3_runner = (
            "import sys; from pathlib import Path; "
            "root=Path.cwd(); sys.path[:0]=[str(root), str(root/'v3')]; "
            "import unittest; "
            "suite=unittest.defaultTestLoader.discover('v3/tests', pattern='test_*.py'); "
            "raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())"
        )
        controls.append(
            (
                "V3_REGRESSION",
                "integration",
                [sys.executable, "-c", v3_runner],
                ROOT,
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
        "schema": "AEOS_MASTER_ASSURANCE_V2",
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