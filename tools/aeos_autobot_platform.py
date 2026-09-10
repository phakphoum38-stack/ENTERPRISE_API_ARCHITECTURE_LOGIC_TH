#!/usr/bin/env python3
"""AEOS Autobot Platform: barriered execution for up to 100 assurance sets.

This module is intentionally an orchestrator, not a replacement for individual
assurance controls. It waits for each wave, freezes evidence, and refuses to
advance on incomplete, stale, or mismatched results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "current" / "AEOS_AUTOBOT_SET_REGISTRY.json"
WAVES = [
    "IDENTITY",
    "SOURCE_CONTRACT",
    "UNIT_REGRESSION",
    "INTEGRATION_BEHAVIOR",
    "SECURITY_ADVERSARIAL",
    "PROVENANCE_EVIDENCE",
    "FORENSIC",
    "INDEPENDENT_REVIEW",
]

TERMINAL = {
    "PASSED",
    "FAILED",
    "CANCELLED",
    "TIMED_OUT",
    "INFRA_FAILED",
    "STALE",
    "UNKNOWN",
    "HOLD",
}


@dataclass(frozen=True)
class SetResult:
    set_id: str
    name: str
    wave: str
    state: str
    returncode: int | None
    command: str
    cwd: str
    duration_seconds: float
    source_sha: str
    iteration_id: str
    evidence_id: str
    detail: str


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"cannot determine source SHA: {result.stdout.strip()}")
    return result.stdout.strip()


def _evidence_id(set_id: str, returncode: int | None, detail: str, source_sha: str, iteration_id: str) -> str:
    payload = f"{set_id}|{returncode}|{detail}|{source_sha}|{iteration_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _powershell_command(command: str) -> list[str]:
    # Windows PowerShell is the execution backend. The orchestrator still
    # controls cwd, environment, timeout and command text at the set boundary.
    executable = os.environ.get("AEOS_POWERSHELL", "powershell.exe")
    return [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]


def _run_set(item: dict[str, Any], iteration_id: str, source_sha: str) -> SetResult:
    set_id = str(item["set_id"])
    name = str(item["name"])
    wave = str(item["wave"])
    command = str(item.get("command", ""))
    cwd = str(item.get("cwd", str(ROOT)))
    timeout = int(item.get("timeout_seconds", 900))

    if item.get("status", "active") != "active":
        detail = "set_not_active:registration_required"
        return SetResult(set_id, name, wave, "HOLD", None, command, cwd, 0.0,
                         source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    if not command:
        detail = "control_missing:command"
        return SetResult(set_id, name, wave, "HOLD", None, command, cwd, 0.0,
                         source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    if not Path(cwd).is_dir():
        detail = "cwd_missing"
        return SetResult(set_id, name, wave, "INFRA_FAILED", None, command, cwd, 0.0,
                         source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)

    started = time.monotonic()
    try:
        if platform.system() == "Windows":
            argv = _powershell_command(command)
        else:
            # CI/Linux may execute PowerShell if pwsh is supplied through the
            # environment; this keeps the adapter testable without changing the
            # orchestration contract.
            executable = os.environ.get("AEOS_POWERSHELL", "pwsh")
            argv = [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]
        proc = subprocess.run(
            argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
        )
        duration = round(time.monotonic() - started, 6)
        detail = proc.stdout.strip()[-12000:]
        allowed = {int(x) for x in item.get("allowed_exit_codes", [0])}
        state = "PASSED" if proc.returncode in allowed else "FAILED"
        return SetResult(set_id, name, wave, state, proc.returncode, command, cwd,
                         duration, source_sha, iteration_id,
                         _evidence_id(set_id, proc.returncode, detail, source_sha, iteration_id), detail)
    except subprocess.TimeoutExpired as exc:
        duration = round(time.monotonic() - started, 6)
        detail = f"timeout:{timeout}s" + (f" output={str(exc.output)[-4000:]}" if exc.output else "")
        return SetResult(set_id, name, wave, "TIMED_OUT", None, command, cwd,
                         duration, source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    except (OSError, ValueError) as exc:
        duration = round(time.monotonic() - started, 6)
        detail = f"execution_error:{type(exc).__name__}:{exc}"
        return SetResult(set_id, name, wave, "INFRA_FAILED", None, command, cwd,
                         duration, source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)


def _validate_registry(registry: dict[str, Any]) -> None:
    sets = registry.get("sets")
    if not isinstance(sets, list) or not sets:
        raise ValueError("registry_empty")
    if len(sets) > 100:
        raise ValueError("registry_exceeds_100_sets")
    ids = [str(item.get("set_id", "")) for item in sets]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("registry_set_id_invalid_or_duplicate")
    for item in sets:
        if str(item.get("wave")) not in WAVES:
            raise ValueError(f"invalid_wave:{item.get('set_id')}")


def _write_manifest(output: Path, iteration_id: str, source_sha: str, results: list[SetResult], decision: str) -> None:
    manifest = {
        "schema_version": "1.0",
        "platform": "AEOS_AUTOBOT_PLATFORM",
        "iteration_id": iteration_id,
        "source_sha": source_sha,
        "decision": decision,
        "barrier_rule": "all required sets in a wave must be terminal before advancing",
        "results": [asdict(result) for result in results],
    }
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    output.with_suffix(output.suffix + ".sha256").write_text(
        hashlib.sha256(raw).hexdigest() + "  " + output.name + "\n", encoding="utf-8"
    )


def run_platform(registry_path: Path, output: Path, max_workers: int) -> int:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    _validate_registry(registry)
    source_sha = _git_sha()
    iteration_id = uuid.uuid4().hex
    results: list[SetResult] = []
    sets = registry["sets"]

    # Wave barrier: controls inside a wave run in parallel, but the next wave
    # cannot start until every set in the current wave is terminal.
    for wave in WAVES:
        wave_sets = [item for item in sets if str(item.get("wave")) == wave]
        if not wave_sets:
            continue
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_run_set, item, iteration_id, source_sha) for item in wave_sets]
            wave_results = [future.result() for future in as_completed(futures)]
        if any(result.state not in TERMINAL for result in wave_results):
            raise RuntimeError(f"barrier_violation:{wave}")
        results.extend(sorted(wave_results, key=lambda r: r.set_id))
        # A failed/held wave is a safety brake. It is recorded; repair/retry is
        # deliberately a separate decision loop so the runner never silently
        # changes source while evidence from this snapshot is still being used.
        if any(result.state not in {"PASSED"} for result in wave_results):
            decision = "HOLD"
            _write_manifest(output, iteration_id, source_sha, results, decision)
            return 2

    decision = "READY_TO_MERGE" if results and all(r.state == "PASSED" for r in results) else "HOLD"
    _write_manifest(output, iteration_id, source_sha, results, decision)
    return 0 if decision == "READY_TO_MERGE" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="AEOS 100-set Autobot Platform")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=ROOT / "aeos_autobot_manifest.json")
    parser.add_argument("--max-workers", type=int, default=16)
    args = parser.parse_args()
    if not 1 <= args.max_workers <= 100:
        parser.error("--max-workers must be between 1 and 100")
    try:
        return run_platform(args.registry, args.output, args.max_workers)
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"AEOS AUTOBOT HOLD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
