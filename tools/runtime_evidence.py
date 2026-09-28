"""Runtime evidence projection over the existing shared lifecycle evidence plane.

This is the Research OS runtime "black box" view. It does not create a second
ledger: it reads and verifies the canonical append-only lifecycle ledger.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from tools.lifecycle_evidence import LifecycleEvidence, LifecycleEvidenceLedger


@dataclass(frozen=True)
class RuntimeEvidenceSnapshot:
    project_id: str
    correlation_id: str
    source_sha: str
    terminal_state: str
    records: tuple[LifecycleEvidence, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "correlation_id": self.correlation_id,
            "source_sha": self.source_sha,
            "terminal_state": self.terminal_state,
            "records": [asdict(record) for record in self.records],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)


def capture_runtime_evidence(
    ledger: LifecycleEvidenceLedger,
    *,
    project_id: str,
    correlation_id: str,
    expected_source_sha: str,
) -> RuntimeEvidenceSnapshot:
    errors = ledger.validate_chain(
        correlation_id=correlation_id,
        expected_source_sha=expected_source_sha,
        expected_project_id=project_id,
    )
    if errors:
        raise ValueError("runtime evidence validation failed: " + "; ".join(errors))
    records = tuple(
        record
        for record in ledger.read()
        if record.correlation_id == correlation_id
    )
    if not records:
        raise ValueError("runtime evidence is missing")
    return RuntimeEvidenceSnapshot(
        project_id=project_id,
        correlation_id=correlation_id,
        source_sha=expected_source_sha,
        terminal_state=records[-1].state,
        records=records,
    )


__all__ = ["RuntimeEvidenceSnapshot", "capture_runtime_evidence"]
