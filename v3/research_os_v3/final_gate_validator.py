from __future__ import annotations

from dataclasses import dataclass

from .final_gate_evidence import FinalGateEvidence, canonical_sha256


@dataclass(frozen=True)
class FinalGateResult:
    passed: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"passed": self.passed, "reasons": list(self.reasons)}


def validate_final_gate(
    evidence: FinalGateEvidence,
    *,
    expected_workflow_id: str,
    expected_run_id: str,
    expected_execution_id: str,
    required_terminal_status: str = "passed",
) -> FinalGateResult:
    reasons: list[str] = []

    if evidence.workflow_id != expected_workflow_id:
        reasons.append("workflow identity mismatch")
    if evidence.run_id != expected_run_id:
        reasons.append("run identity mismatch")
    if evidence.execution_id != expected_execution_id:
        reasons.append("execution identity mismatch")
    if evidence.terminal_status != required_terminal_status:
        reasons.append("terminal status is not passed")
    if not evidence.delivery_ids:
        reasons.append("delivery lineage is empty")
    if not evidence.resource_versions:
        reasons.append("resource lineage is empty")

    canonical_payload = {
        "workflow_id": evidence.workflow_id,
        "run_id": evidence.run_id,
        "execution_id": evidence.execution_id,
        "delivery_ids": list(evidence.delivery_ids),
        "resource_versions": list(evidence.resource_versions),
        "terminal_status": evidence.terminal_status,
        "extra": dict(evidence.extra),
    }
    if evidence.canonical_sha256 != canonical_sha256(canonical_payload):
        reasons.append("canonical evidence SHA mismatch")

    return FinalGateResult(passed=not reasons, reasons=tuple(reasons))
