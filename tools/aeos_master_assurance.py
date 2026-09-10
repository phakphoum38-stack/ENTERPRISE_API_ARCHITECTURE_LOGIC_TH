#!/usr/bin/env python3
"""AEOS Master Assurance orchestrator.

Runs independent assurance controls in one invocation while preserving per-control
failure isolation and producing one machine-readable assurance manifest.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ControlResult:
    control_id: str
    class_name: str
    status: str
    command: list[str]
    returncode: int
    duration_seconds: float
    detail: str = ""


def run_control(control_id: str, class_name: str, command: list[str]) -> ControlResult:
    started = time.monotonic()
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    duration = round(time.monotonic() - started, 3)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    detail = output[-4000:] if output else ""
    return ControlResult(
        control_id=control_id,
        class_name=class_name,
        status="PASS" if proc.returncode == 0 else "FAIL",
        command=command,
        returncode=proc.returncode,
        duration_seconds=duration,
        detail=detail,
    )


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def git_base_sha() -> str:
    value = os.environ.get("AEOS_BASE_SHA", "").strip()
    return value


def discover_controls() -> list[tuple[str, str, list[str]]]:
    controls: list[tuple[str, str, list[str]]] = []

    # Identity / canonical revision.
    expected = os.environ.get("AEOS_EXPECTED_SHA", "").strip()
    if expected:
        controls.append(
            (
                "IDENTITY_SHA",
                "identity",
                [sys.executable, "-c", f"import subprocess; actual=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); expected={expected!r}; print(actual); assert actual == expected, f'expected {{expected}}, got {{actual}}'"],
            )
        )

    # Compile all assurance-related Python source and tests.
    compile_paths = [p for p in (ROOT / "owner_special", ROOT / "tools") if p.exists()]
    if compile_paths:
        controls.append(
            (
                "PYTHON_COMPILE",
                "static",
                [sys.executable, "-m", "compileall", "-q", *(str(p.relative_to(ROOT)) for p in compile_paths)],
            )
        )

    # AEOS source-semantic and assurance validators are first-class controls.
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
            controls.append((path.stem.upper(), "validator", args))

    # Run the AEOS regression suite without making any one test certify another.
    test_dir = ROOT / "owner_special" / "tests"
    if test_dir.is_dir():
        controls.append(
            (
                "AEOS_REGRESSION",
                "behavioral",
                [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir.relative_to(ROOT)), "-p", "test_aeos_*.py", "-v"],
            )
        )

    # Optional V3 regression is included when present; this remains an independent control.
    v3_test_dir = ROOT / "v3" / "tests"
    if v3_test_dir.is_dir():
        controls.append(
            (
                "V3_REGRESSION",
                "integration",
                [sys.executable, "-m", "unittest", "discover", "-s", "v3/tests", "-p", "test_*.py", "-v"],
            )
        )

    return controls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="aeos_master_assurance_manifest.json")
    args = parser.parse_args()

    results: list[ControlResult] = []
    controls = discover_controls()
    if not controls:
        print("AEOS_MASTER_ASSURANCE=FAIL: no executable controls discovered")
        return 2

    for control_id, class_name, command in controls:
        result = run_control(control_id, class_name, command)
        results.append(result)
        print(f"[{result.status}] {result.control_id} ({result.duration_seconds}s)")
        if result.status == "FAIL":
            print(result.detail)

    failed = [r for r in results if r.status != "PASS"]
    manifest = {
        "schema": "AEOS_MASTER_ASSURANCE_V1",
        "assurance_run_id": os.environ.get("AEOS_ASSURANCE_RUN_ID", f"local-{int(time.time())}"),
        "source_sha": git_sha(),
        "base_sha": git_base_sha() or None,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "control_count": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "decision": "FAIL" if failed else "PASS",
        "controls": [asdict(r) for r in results],
    }
    output = ROOT / args.output
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("assurance_run_id", "source_sha", "control_count", "passed", "failed", "decision")}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
