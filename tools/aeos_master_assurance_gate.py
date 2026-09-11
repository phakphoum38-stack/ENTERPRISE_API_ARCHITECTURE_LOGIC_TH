#!/usr/bin/env python3
"""Fail-closed decision boundary between execution evidence and owner authority.

The Autobot platform produces execution evidence. This module consumes that
artifact plus an externally produced assurance proof and delegates the final
readiness decision to MasterAssuranceComposition. It never executes controls,
creates verification proof, approves, or merges.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from tools.aeos_autobot_platform import SetResult
from tools.aeos_master_composition import (
    compose_master_assurance,
    load_proof,
    snapshot_from_results,
)


def _load_execution_manifest(path: Path) -> tuple[Mapping[str, Any], str]:
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("execution_manifest_root_invalid")
    declared = path.with_suffix(path.suffix + ".sha256").read_text(encoding="utf-8").strip().split()
    if not declared or declared[0] != hashlib.sha256(raw).hexdigest():
        raise ValueError("execution_manifest_integrity_invalid")
    return payload, hashlib.sha256(raw).hexdigest()


def _results(payload: Mapping[str, Any]) -> list[SetResult]:
    rows = payload.get("results")
    if not isinstance(rows, list) or not rows:
        raise ValueError("execution_results_missing")
    results: list[SetResult] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("execution_result_invalid")
        results.append(SetResult(
            set_id=str(row["set_id"]), name=str(row["name"]), wave=str(row["wave"]),
            state=str(row["state"]), returncode=row.get("returncode"),
            command=str(row["command"]), cwd=str(row["cwd"]),
            duration_seconds=float(row["duration_seconds"]),
            source_sha=str(row["source_sha"]), iteration_id=str(row["iteration_id"]),
            evidence_id=str(row["evidence_id"]), detail=str(row["detail"]),
        ))
    return results


def run_gate(execution_manifest: Path, assurance_proof: Path, output: Path) -> int:
    payload, manifest_digest = _load_execution_manifest(execution_manifest)
    source_sha = str(payload.get("source_sha", ""))
    iteration_id = str(payload.get("iteration_id", ""))
    results = _results(payload)
    if any(result.source_sha != source_sha or result.iteration_id != iteration_id for result in results):
        raise ValueError("execution_result_identity_mismatch")

    snapshot = snapshot_from_results(
        iteration_id=iteration_id,
        source_sha=source_sha,
        results=results,
        execution_manifest_digest=manifest_digest,
    )
    proof = load_proof(assurance_proof)
    composition = compose_master_assurance(snapshot=snapshot, proof=proof)
    record = composition.canonical()
    record["composition_digest"] = composition.digest()
    record["execution_manifest_digest"] = manifest_digest
    record["authority"] = "OWNER_ONLY"

    raw = json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    output.with_suffix(output.suffix + ".sha256").write_text(
        hashlib.sha256(raw).hexdigest() + "  " + output.name + "\n", encoding="utf-8"
    )
    print(f"AEOS MASTER COMPOSITION: {composition.decision} ({composition.reason})")
    return 0 if composition.decision == "READY_FOR_OWNER_AUTHORITY" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="AEOS fail-closed master assurance boundary")
    parser.add_argument("--execution-manifest", type=Path, required=True)
    parser.add_argument("--assurance-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("aeos_master_composition.json"))
    args = parser.parse_args()
    try:
        return run_gate(args.execution_manifest, args.assurance_proof, args.output)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"AEOS MASTER COMPOSITION HOLD: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
