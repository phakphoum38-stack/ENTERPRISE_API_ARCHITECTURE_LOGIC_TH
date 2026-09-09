"""Deterministic decision-replay boundary for AEOS."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class DecisionReplayError(ValueError):
    """Raised when a decision cannot be replayed exactly."""


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    baseline_sha: str
    contract_sha256: str
    policy_sha256: str
    input_digest: str
    output_digest: str
    evidence_refs: tuple[str, ...]


def _sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def record_decision(*, decision_id: str, baseline_sha: str, contract_sha256: str, policy_sha256: str, inputs: Mapping[str, Any], output: Mapping[str, Any], evidence_refs: tuple[str, ...]) -> DecisionRecord:
    if not isinstance(decision_id, str) or not decision_id:
        raise DecisionReplayError("decision_id required")
    for value, name, size in ((baseline_sha, "baseline_sha", 40), (contract_sha256, "contract_sha256", 64), (policy_sha256, "policy_sha256", 64)):
        if not isinstance(value, str) or len(value) != size or any(c not in "0123456789abcdef" for c in value):
            raise DecisionReplayError(f"invalid {name}")
    if not isinstance(inputs, Mapping) or not isinstance(output, Mapping):
        raise DecisionReplayError("inputs and output must be mappings")
    if not isinstance(evidence_refs, tuple) or not evidence_refs or len(set(evidence_refs)) != len(evidence_refs):
        raise DecisionReplayError("unique evidence_refs required")
    return DecisionRecord(decision_id, baseline_sha, contract_sha256, policy_sha256, _sha256(inputs), _sha256(output), evidence_refs)


def replay_decision(*, record: DecisionRecord, inputs: Mapping[str, Any], output: Mapping[str, Any], baseline_sha: str, contract_sha256: str, policy_sha256: str) -> bool:
    if not isinstance(record, DecisionRecord):
        raise DecisionReplayError("DecisionRecord required")
    if (baseline_sha, contract_sha256, policy_sha256) != (record.baseline_sha, record.contract_sha256, record.policy_sha256):
        raise DecisionReplayError("decision binding changed")
    if _sha256(inputs) != record.input_digest:
        raise DecisionReplayError("decision input replay mismatch")
    if _sha256(output) != record.output_digest:
        raise DecisionReplayError("decision output replay mismatch")
    return True
