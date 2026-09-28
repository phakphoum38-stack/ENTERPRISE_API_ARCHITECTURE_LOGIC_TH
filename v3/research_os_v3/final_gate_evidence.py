from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FinalGateEvidence:
    """Immutable identity binding for one workflow causal lineage."""

    workflow_id: str
    run_id: str
    execution_id: str
    canonical_sha256: str
    delivery_ids: tuple[str, ...] = ()
    resource_versions: tuple[str, ...] = ()
    terminal_status: str = "unknown"
    extra: tuple[tuple[str, object], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
            "execution_id": self.execution_id,
            "canonical_sha256": self.canonical_sha256,
            "delivery_ids": list(self.delivery_ids),
            "resource_versions": list(self.resource_versions),
            "terminal_status": self.terminal_status,
            "extra": dict(self.extra),
        }


def build_final_gate_evidence(
    *,
    workflow_id: str,
    run_id: str,
    execution_id: str,
    delivery_ids: tuple[str, ...] = (),
    resource_versions: tuple[str, ...] = (),
    terminal_status: str = "unknown",
    extra: Mapping[str, object] | None = None,
) -> FinalGateEvidence:
    identity = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "execution_id": execution_id,
        "delivery_ids": list(delivery_ids),
        "resource_versions": list(resource_versions),
        "terminal_status": terminal_status,
        "extra": dict(extra or {}),
    }
    return FinalGateEvidence(
        workflow_id=workflow_id,
        run_id=run_id,
        execution_id=execution_id,
        canonical_sha256=canonical_sha256(identity),
        delivery_ids=delivery_ids,
        resource_versions=resource_versions,
        terminal_status=terminal_status,
        extra=tuple(sorted((extra or {}).items())),
    )


def validate_final_gate_evidence(
    evidence: FinalGateEvidence,
    *,
    expected_workflow_id: str,
    expected_run_id: str,
    expected_execution_id: str,
) -> None:
    if evidence.workflow_id != expected_workflow_id:
        raise ValueError("workflow identity mismatch")
    if evidence.run_id != expected_run_id:
        raise ValueError("run identity mismatch")
    if evidence.execution_id != expected_execution_id:
        raise ValueError("execution identity mismatch")
    if not evidence.canonical_sha256:
        raise ValueError("canonical identity is required")
