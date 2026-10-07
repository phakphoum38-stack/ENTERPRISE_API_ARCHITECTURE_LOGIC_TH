#!/usr/bin/env python3
"""Research OS External Validation Plane.

Read-only, exact-SHA validation over existing canonical validators.
This runner never mutates source, approves, merges, or releases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_EXTERNAL_VALIDATION_CONTRACT.json"
EVIDENCE_SCHEMA = "research-os.external-validation-evidence.v1"


def git_sha(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_validator(root: Path, validator_id: str, command: list[str], source_sha: str) -> dict:
    rendered = [part.replace("{source_sha}", source_sha) for part in command]
    completed = subprocess.run(
        [sys.executable, *rendered],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=300,
    )
    stdout = completed.stdout[-12000:]
    stderr = completed.stderr[-12000:]
    return {
        "id": validator_id,
        "command": rendered,
        "exit_code": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "output": stdout,
        "error": stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", default="evidence/external-validation.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    actual_sha = git_sha(root)
    if actual_sha != args.source_sha:
        print("EXTERNAL_VALIDATION=HOLD source_sha_mismatch")
        return 2

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    results = []
    for validator in contract["validators"]:
        try:
            results.append(run_validator(
                root, validator["id"], validator["command"], args.source_sha
            ))
        except subprocess.TimeoutExpired:
            results.append({
                "id": validator["id"],
                "command": validator["command"],
                "exit_code": None,
                "status": "FAIL",
                "stdout_sha256": None,
                "stderr_sha256": None,
                "output": "",
                "error": "validator_timeout",
            })

    failed = [item["id"] for item in results if item["status"] != "PASS"]
    status = "FAIL" if failed else "PASS"
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "contract_id": contract["contract_id"],
        "contract_sha256": file_digest(CONTRACT),
        "source_sha": args.source_sha,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "validator_count": len(results),
        "validators": results,
        "excluded_path_segment": "efi",
        "authority": "evidence_projection_only",
        "release_authority": "FINAL_GATE"
    }

    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"EXTERNAL_VALIDATION={status}")
    print(f"SOURCE_SHA={args.source_sha}")
    print(f"VALIDATORS={len(results)}")
    print(f"FAILED={','.join(failed) if failed else 'NONE'}")
    print(f"EVIDENCE={output.relative_to(root).as_posix()}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
