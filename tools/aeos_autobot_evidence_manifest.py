#!/usr/bin/env python3
"""Deterministic, fail-closed evidence ledger for AEOS Autobot waves."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

from tools.aeos_autobot_state_machine import Evidence, ResultState, Snapshot

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SnapshotLock:
    iteration_id: str
    source_sha: str
    test_batch_id: str
    workflow_run_id: str
    control_set: tuple[str, ...]
    started_at: str
    completed_at: str

    def validate(self) -> None:
        if not self.iteration_id or not self.test_batch_id or not self.workflow_run_id:
            raise ValueError("snapshot_identity_missing")
        if not SHA_RE.fullmatch(self.source_sha):
            raise ValueError("invalid_source_sha")
        if not self.control_set or len(set(self.control_set)) != len(self.control_set):
            raise ValueError("invalid_control_set")
        if not self.started_at or not self.completed_at:
            raise ValueError("snapshot_time_missing")


def evidence_id(snapshot: Snapshot, result_state: ResultState) -> str:
    payload = f"{snapshot.identity()}|{result_state.value}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_json(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _evidence_record(item: Evidence, lock: SnapshotLock) -> dict:
    snapshot = item.snapshot
    if snapshot.iteration_id != lock.iteration_id or snapshot.source_sha != lock.source_sha:
        raise ValueError("stale_or_cross_iteration_evidence")
    if snapshot.wave_id == "":
        raise ValueError("missing_wave_id")
    expected = evidence_id(snapshot, item.result_state)
    if item.evidence_id != expected:
        raise ValueError(f"evidence_id_mismatch:{snapshot.set_id}")
    if not EVIDENCE_RE.fullmatch(item.evidence_id):
        raise ValueError(f"invalid_evidence_id:{snapshot.set_id}")
    return {
        "iteration_id": snapshot.iteration_id,
        "source_sha": snapshot.source_sha,
        "set_id": snapshot.set_id,
        "wave_id": snapshot.wave_id,
        "command": snapshot.command,
        "cwd": snapshot.cwd,
        "result_state": item.result_state.value,
        "evidence_id": item.evidence_id,
    }


def build_manifest(lock: SnapshotLock, wave_id: str, evidence: Iterable[Evidence], decision: ResultState) -> dict:
    lock.validate()
    items = list(evidence)
    if not items:
        raise ValueError("empty_evidence")
    if any(item.snapshot.wave_id != wave_id for item in items):
        raise ValueError("wave_mismatch")
    records = [_evidence_record(item, lock) for item in items]
    set_ids = [item["set_id"] for item in records]
    if len(set_ids) != len(set(set_ids)):
        raise ValueError("duplicate_set_evidence")
    if set(set_ids) != set(lock.control_set):
        raise ValueError("incomplete_control_set")
    if any(item["result_state"] in {ResultState.RUNNING.value, ResultState.QUEUED.value} for item in records):
        raise ValueError("incomplete_evidence")
    if decision == ResultState.PASSED and any(item["result_state"] != ResultState.PASSED.value for item in records):
        raise ValueError("decision_mismatch")
    if decision == ResultState.PASSED and len(records) != len(lock.control_set):
        raise ValueError("incomplete_pass_decision")

    manifest = {
        "schema_version": "1.0",
        "contract": "AEOS_AUTOBOT_EVIDENCE_MANIFEST",
        "iteration_id": lock.iteration_id,
        "source_sha": lock.source_sha,
        "test_batch_id": lock.test_batch_id,
        "workflow_run_id": lock.workflow_run_id,
        "wave_id": wave_id,
        "started_at": lock.started_at,
        "completed_at": lock.completed_at,
        "decision": decision.value,
        "evidence": sorted(records, key=lambda item: (item["set_id"], item["evidence_id"])),
        "manifest_sha256": "",
    }
    digest = hashlib.sha256(canonical_json(manifest)).hexdigest()
    manifest["manifest_sha256"] = digest
    return manifest


def write_manifest(manifest: dict, path: str | Path) -> tuple[str, str]:
    target = Path(path)
    payload = canonical_json(manifest)
    target.write_bytes(payload)
    sidecar_digest = hashlib.sha256(payload).hexdigest()
    sidecar = target.with_name(target.name + ".sha256")
    sidecar.write_text(f"{sidecar_digest}  {target.name}\n", encoding="utf-8")
    return sidecar_digest, str(sidecar)


def verify_manifest(path: str | Path) -> None:
    target = Path(path)
    payload = target.read_bytes()
    manifest = json.loads(payload.decode("utf-8"))
    recorded = manifest.get("manifest_sha256")
    if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded):
        raise ValueError("invalid_manifest_sha256")
    probe = dict(manifest)
    probe["manifest_sha256"] = ""
    expected = hashlib.sha256(canonical_json(probe)).hexdigest()
    if recorded != expected:
        raise ValueError("manifest_digest_mismatch")
    sidecar = target.with_name(target.name + ".sha256")
    if not sidecar.is_file():
        raise ValueError("missing_manifest_sidecar")
    line = sidecar.read_text(encoding="utf-8").strip()
    expected_sidecar = hashlib.sha256(payload).hexdigest()
    if line != f"{expected_sidecar}  {target.name}":
        raise ValueError("manifest_sidecar_mismatch")


if __name__ == "__main__":
    print("AEOS_AUTOBOT_EVIDENCE_MANIFEST=READY")
