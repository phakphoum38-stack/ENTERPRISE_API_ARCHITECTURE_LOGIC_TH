#!/usr/bin/env python3
"""AEOS Autobot Platform: canonical, barriered and bounded execution.

The platform is fail-closed. The assurance registry is the canonical authority
for set identity, lifecycle and wave. The execution registry is only a derived
projection containing executable metadata. It may never invent, rename, move,
or activate a canonical set.
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
DEFAULT_CANONICAL_REGISTRY = ROOT / "current" / "AEOS_AUTOBOT_ASSURANCE_SET_REGISTRY.json"
WAVE_MAP = {
    "W0": "IDENTITY",
    "W1": "SOURCE_CONTRACT",
    "W2": "UNIT_REGRESSION",
    "W3": "INTEGRATION_BEHAVIOR",
    "W4": "SECURITY_ADVERSARIAL",
    "W5": "PROVENANCE_EVIDENCE",
    "W6": "FORENSIC",
    "W7": "INDEPENDENT_REVIEW",
}
WAVES = list(WAVE_MAP.values())
CANONICAL_STATUS = {"IMPLEMENTED", "PLANNED"}
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
    executable = os.environ.get("AEOS_POWERSHELL", "powershell.exe")
    return [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]


def _projection_status(canonical_status: str, execution_status: str) -> bool:
    # Only canonical lifecycle can activate a set. The projection may not
    # upgrade PLANNED to executable or downgrade an IMPLEMENTED declaration.
    if canonical_status == "IMPLEMENTED":
        return execution_status == "active"
    return execution_status == "planned"


def _validate_registry(registry: dict[str, Any], canonical: dict[str, Any]) -> dict[str, dict[str, Any]]:
    canonical_sets = canonical.get("sets")
    sets = registry.get("sets")
    if canonical.get("contract") != "AEOS_AUTOBOT_ASSURANCE_SET_REGISTRY":
        raise ValueError("canonical_registry_contract_invalid")
    if not isinstance(canonical_sets, list) or len(canonical_sets) != int(canonical.get("set_count", -1)):
        raise ValueError("canonical_registry_set_count_invalid")
    if not isinstance(sets, list):
        raise ValueError("registry_empty")
    if len(sets) > int(registry.get("max_sets", 100)) or len(sets) > 100:
        raise ValueError("registry_exceeds_100_sets")

    canonical_by_id: dict[str, dict[str, Any]] = {}
    for item in canonical_sets:
        set_id = str(item.get("set_id", ""))
        wave = str(item.get("wave", ""))
        status = str(item.get("status", ""))
        if not set_id or set_id in canonical_by_id:
            raise ValueError("canonical_registry_set_id_invalid_or_duplicate")
        if wave not in WAVE_MAP or status not in CANONICAL_STATUS:
            raise ValueError(f"canonical_registry_entry_invalid:{set_id}")
        canonical_by_id[set_id] = item

    projection_ids: set[str] = set()
    projection_by_id: dict[str, dict[str, Any]] = {}
    for item in sets:
        set_id = str(item.get("set_id", ""))
        if not set_id or set_id in projection_ids:
            raise ValueError("registry_set_id_invalid_or_duplicate")
        projection_ids.add(set_id)
        source = canonical_by_id.get(set_id)
        if source is None:
            raise ValueError(f"unknown_set_not_in_canonical:{set_id}")
        if str(item.get("name")) != str(source.get("name")):
            raise ValueError(f"canonical_name_mismatch:{set_id}")
        if str(item.get("wave")) != WAVE_MAP[str(source.get("wave"))]:
            raise ValueError(f"canonical_wave_mismatch:{set_id}")
        execution_status = str(item.get("status", ""))
        if not _projection_status(str(source.get("status")), execution_status):
            raise ValueError(f"canonical_status_mismatch:{set_id}")
        if execution_status == "active":
            required = ("command", "cwd", "source_sha_policy", "timeout_seconds", "allowed_exit_codes", "evidence_policy", "repair_policy", "scope", "changed_files", "risk_level")
            missing = [field for field in required if field not in item]
            if missing:
                raise ValueError(f"active_set_metadata_missing:{set_id}:{','.join(missing)}")
            if not isinstance(item["scope"], int) or not isinstance(item["changed_files"], int) or not isinstance(item["risk_level"], int):
                raise ValueError(f"active_set_safety_metadata_invalid:{set_id}")
            if item["scope"] < 0 or item["changed_files"] < 0 or item["risk_level"] < 0:
                raise ValueError(f"active_set_safety_metadata_negative:{set_id}")
        projection_by_id[set_id] = item

    # Every canonical IMPLEMENTED set is required. A projection omission is
    # therefore a HOLD rather than an implicit reduction of the assurance set.
    required_ids = {sid for sid, item in canonical_by_id.items() if item["status"] == "IMPLEMENTED"}
    if not required_ids.issubset(projection_ids):
        missing = sorted(required_ids - projection_ids)
        raise ValueError(f"canonical_required_set_missing:{','.join(missing)}")
    if not sets:
        raise ValueError("registry_empty")
    return projection_by_id


def _run_set(item: dict[str, Any], iteration_id: str, source_sha: str, deadline: float, limits: dict[str, int]) -> SetResult:
    set_id = str(item["set_id"])
    name = str(item["name"])
    wave = str(item["wave"])
    command = str(item.get("command", ""))
    cwd = str(item.get("cwd", str(ROOT)))
    timeout = float(item.get("timeout_seconds", 900))

    if item.get("status", "") != "active":
        detail = "set_not_active:registration_required"
        return SetResult(set_id, name, wave, "HOLD", None, command, cwd, 0.0,
                         source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    if not command:
        detail = "control_missing:command"
        return SetResult(set_id, name, wave, "HOLD", None, command, cwd, 0.0,
                         source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    if item["scope"] > limits["max_scope"]:
        detail = f"scope_limit_exceeded:{item['scope']}>{limits['max_scope']}"
        return SetResult(set_id, name, wave, "HOLD", None, command, cwd, 0.0,
                         source_sha, iteration_id, _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    if item["changed_files"] > limits["max_changed_files"]:
        detail = f"changed_files_limit_exceeded:{item['changed_files']}>{limits['max_changed_files']}"
        return SetResult(set_id, name, wave, "HOLD", None, command, cwd, 0.0,
                         source_sha, iteration_id, _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    if item["risk_level"] > limits["max_risk_level"]:
        detail = f"risk_limit_exceeded:{item['risk_level']}>{limits['max_risk_level']}"
        return SetResult(set_id, name, wave, "HOLD", None, command, cwd, 0.0,
                         source_sha, iteration_id, _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    if not Path(cwd).is_dir():
        detail = "cwd_missing"
        return SetResult(set_id, name, wave, "INFRA_FAILED", None, command, cwd, 0.0,
                         source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        detail = "global_runtime_limit_exceeded"
        return SetResult(set_id, name, wave, "TIMED_OUT", None, command, cwd, 0.0,
                         source_sha, iteration_id, _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)

    effective_timeout = min(timeout, remaining)
    started = time.monotonic()
    try:
        if platform.system() == "Windows":
            argv = _powershell_command(command)
        else:
            executable = os.environ.get("AEOS_POWERSHELL", "pwsh")
            argv = [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]
        proc = subprocess.run(
            argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=effective_timeout, check=False,
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
        detail = f"timeout:{effective_timeout:.6f}s" + (f" output={str(exc.output)[-4000:]}" if exc.output else "")
        return SetResult(set_id, name, wave, "TIMED_OUT", None, command, cwd,
                         duration, source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)
    except (OSError, ValueError) as exc:
        duration = round(time.monotonic() - started, 6)
        detail = f"execution_error:{type(exc).__name__}:{exc}"
        return SetResult(set_id, name, wave, "INFRA_FAILED", None, command, cwd,
                         duration, source_sha, iteration_id,
                         _evidence_id(set_id, None, detail, source_sha, iteration_id), detail)


def _write_manifest(output: Path, iteration_id: str, source_sha: str, results: list[SetResult], decision: str) -> None:
    manifest = {
        "schema_version": "1.0",
        "platform": "AEOS_AUTOBOT_PLATFORM",
        "iteration_id": iteration_id,
        "source_sha": source_sha,
        "decision": decision,
        "authority": "OWNER_ONLY",
        "barrier_rule": "all canonical required sets in a wave must be terminal and PASSED before advancing",
        "results": [asdict(result) for result in results],
    }
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    output.with_suffix(output.suffix + ".sha256").write_text(
        hashlib.sha256(raw).hexdigest() + "  " + output.name + "\n", encoding="utf-8"
    )


def run_platform(registry_path: Path, output: Path, max_workers: int, *, canonical_registry_path: Path | None = None,
                 max_runtime_seconds: float = 3600.0, max_scope: int = 100,
                 max_changed_files: int = 100, max_risk_level: int = 4) -> int:
    if max_runtime_seconds <= 0 or max_scope < 0 or max_changed_files < 0 or max_risk_level < 0:
        raise ValueError("invalid_execution_limits")
    if max_workers < 1 or max_workers > 100:
        raise ValueError("invalid_max_workers")

    canonical_path = canonical_registry_path or DEFAULT_CANONICAL_REGISTRY
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    projection = _validate_registry(registry, canonical)
    source_sha = _git_sha()
    iteration_id = uuid.uuid4().hex
    deadline = time.monotonic() + max_runtime_seconds
    limits = {"max_scope": max_scope, "max_changed_files": max_changed_files, "max_risk_level": max_risk_level}
    results: list[SetResult] = []

    required_by_wave: dict[str, list[dict[str, Any]]] = {wave: [] for wave in WAVES}
    canonical_sets = canonical["sets"]
    for canonical_item in canonical_sets:
        if canonical_item["status"] == "IMPLEMENTED":
            set_id = str(canonical_item["set_id"])
            item = projection[set_id]
            required_by_wave[WAVE_MAP[str(canonical_item["wave"])]] .append(item)

    for wave in WAVES:
        wave_sets = required_by_wave[wave]
        if not wave_sets:
            continue
        if time.monotonic() >= deadline:
            _write_manifest(output, iteration_id, source_sha, results, "HOLD")
            return 2

        pool = ThreadPoolExecutor(max_workers=min(max_workers, len(wave_sets)))
        futures = [pool.submit(_run_set, item, iteration_id, source_sha, deadline, limits) for item in wave_sets]
        wave_results: list[SetResult] = []
        try:
            remaining = max(0.0, deadline - time.monotonic())
            for future in as_completed(futures, timeout=remaining):
                wave_results.append(future.result())
        except TimeoutError:
            for future in futures:
                future.cancel()
            wave_results.extend(
                SetResult(
                    str(item["set_id"]), str(item["name"]), wave, "TIMED_OUT", None,
                    str(item.get("command", "")), str(item.get("cwd", str(ROOT))),
                    0.0, source_sha, iteration_id,
                    _evidence_id(str(item["set_id"]), None, "global_runtime_limit_exceeded", source_sha, iteration_id),
                    "global_runtime_limit_exceeded",
                )
                for item in wave_sets
                if str(item["set_id"]) not in {r.set_id for r in wave_results}
            )
        finally:
            # Do not wait past the global deadline. Each child process also has
            # the remaining budget as its subprocess timeout.
            pool.shutdown(wait=False, cancel_futures=True)

        if len({r.set_id for r in wave_results}) != len(wave_sets):
            missing = {str(item["set_id"]) for item in wave_sets} - {r.set_id for r in wave_results}
            for set_id in sorted(missing):
                item = projection[set_id]
                detail = "global_runtime_limit_exceeded"
                wave_results.append(SetResult(set_id, str(item["name"]), wave, "TIMED_OUT", None,
                                              str(item.get("command", "")), str(item.get("cwd", str(ROOT))), 0.0,
                                              source_sha, iteration_id,
                                              _evidence_id(set_id, None, detail, source_sha, iteration_id), detail))

        wave_results.sort(key=lambda r: r.set_id)
        if any(result.state not in TERMINAL for result in wave_results):
            raise RuntimeError(f"barrier_violation:{wave}")
        results.extend(wave_results)
        if any(result.state != "PASSED" for result in wave_results):
            _write_manifest(output, iteration_id, source_sha, results, "HOLD")
            return 2

    decision = "READY_FOR_OWNER_AUTHORITY" if results and all(r.state == "PASSED" for r in results) else "HOLD"
    _write_manifest(output, iteration_id, source_sha, results, decision)
    return 0 if decision == "READY_FOR_OWNER_AUTHORITY" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="AEOS 100-set Autobot Platform")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--canonical-registry", type=Path, default=DEFAULT_CANONICAL_REGISTRY)
    parser.add_argument("--output", type=Path, default=ROOT / "aeos_autobot_manifest.json")
    parser.add_argument("--max-workers", type=int, default=16)
    parser.add_argument("--max-runtime-seconds", type=float, default=3600.0)
    parser.add_argument("--max-scope", type=int, default=100)
    parser.add_argument("--max-changed-files", type=int, default=100)
    parser.add_argument("--max-risk-level", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.max_workers <= 100:
        parser.error("--max-workers must be between 1 and 100")
    try:
        return run_platform(
            args.registry, args.output, args.max_workers,
            canonical_registry_path=args.canonical_registry,
            max_runtime_seconds=args.max_runtime_seconds,
            max_scope=args.max_scope,
            max_changed_files=args.max_changed_files,
            max_risk_level=args.max_risk_level,
        )
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"AEOS AUTOBOT HOLD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
