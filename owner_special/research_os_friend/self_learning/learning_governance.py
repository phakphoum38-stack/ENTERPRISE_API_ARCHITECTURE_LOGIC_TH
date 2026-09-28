from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence


@dataclass(frozen=True)
class LearningSource:
    source_id: str
    source_type: str
    reference: str
    observed_at: str


@dataclass(frozen=True)
class KnowledgeConflict:
    conflict_id: str
    subject_id: str
    competing_ids: tuple[str, ...]
    status: str
    reason: str


@dataclass(frozen=True)
class TransferAssessment:
    transfer_id: str
    source_knowledge_id: str
    target_domain: str
    applicable: bool
    evidence_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class LearningCorrection:
    correction_id: str
    target_id: str
    previous_state: str
    corrected_state: str
    reason: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryState:
    recovery_id: str
    goal: str
    current_state: str
    completed: tuple[str, ...]
    pending: tuple[str, ...]
    blocked: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    next_step: str


class LearningGovernanceBoundary:
    """Data-only governance for provenance, conflict, transfer, correction, recovery."""

    def source(
        self,
        *,
        source_type: str,
        reference: str,
        observed_at: str,
    ) -> LearningSource:
        if not source_type.strip() or not reference.strip() or not observed_at.strip():
            raise ValueError("source metadata is required")
        source_id = self._hash({
            "source_type": source_type,
            "reference": reference,
            "observed_at": observed_at,
        })
        return LearningSource(source_id, source_type, reference, observed_at)

    def conflict(
        self,
        *,
        subject_id: str,
        competing_ids: Sequence[str],
        reason: str,
        status: str = "CONFLICTED",
    ) -> KnowledgeConflict:
        if not subject_id.strip() or len(competing_ids) < 2 or not reason.strip():
            raise ValueError("conflict requires subject, competing records, and reason")
        if status != "CONFLICTED":
            raise ValueError("unresolved conflict must remain CONFLICTED")
        ids = tuple(sorted(set(competing_ids)))
        if len(ids) < 2:
            raise ValueError("conflict requires distinct competing records")
        return KnowledgeConflict(
            self._hash({
                "subject_id": subject_id,
                "competing_ids": ids,
                "reason": reason,
                "status": status,
            }),
            subject_id,
            ids,
            status,
            reason,
        )

    def transfer(
        self,
        *,
        source_knowledge_id: str,
        target_domain: str,
        applicable: bool,
        evidence_ids: Sequence[str],
        limitations: Sequence[str] = (),
    ) -> TransferAssessment:
        if not source_knowledge_id.strip() or not target_domain.strip():
            raise ValueError("transfer source and target are required")
        if applicable and not evidence_ids:
            raise ValueError("applicable transfer requires evidence")
        ids = tuple(sorted(set(evidence_ids)))
        limits = tuple(sorted(limitations))
        if any(not item.strip() for item in limits):
            raise ValueError("transfer limitation cannot be empty")
        return TransferAssessment(
            self._hash({
                "source_knowledge_id": source_knowledge_id,
                "target_domain": target_domain,
                "applicable": applicable,
                "evidence_ids": ids,
                "limitations": limits,
            }),
            source_knowledge_id,
            target_domain,
            applicable,
            ids,
            limits,
        )

    def correction(
        self,
        *,
        target_id: str,
        previous_state: str,
        corrected_state: str,
        reason: str,
        evidence_ids: Sequence[str],
    ) -> LearningCorrection:
        if not target_id.strip() or not previous_state.strip() or not corrected_state.strip():
            raise ValueError("correction state is required")
        if not reason.strip():
            raise ValueError("correction reason is required")
        if not evidence_ids:
            raise ValueError("correction requires evidence")
        ids = tuple(sorted(set(evidence_ids)))
        return LearningCorrection(
            self._hash({
                "target_id": target_id,
                "previous_state": previous_state,
                "corrected_state": corrected_state,
                "reason": reason,
                "evidence_ids": ids,
            }),
            target_id,
            previous_state,
            corrected_state,
            reason,
            ids,
        )

    def recovery(
        self,
        *,
        goal: str,
        current_state: str,
        completed: Sequence[str],
        pending: Sequence[str],
        blocked: Sequence[str],
        evidence_ids: Sequence[str],
        next_step: str,
    ) -> RecoveryState:
        if not goal.strip() or not current_state.strip() or not next_step.strip():
            raise ValueError("recovery state requires goal, state, and next step")
        return RecoveryState(
            self._hash({
                "goal": goal,
                "current_state": current_state,
                "completed": tuple(sorted(set(completed))),
                "pending": tuple(sorted(set(pending))),
                "blocked": tuple(sorted(set(blocked))),
                "evidence_ids": tuple(sorted(set(evidence_ids))),
                "next_step": next_step,
            }),
            goal,
            current_state,
            tuple(sorted(set(completed))),
            tuple(sorted(set(pending))),
            tuple(sorted(set(blocked))),
            tuple(sorted(set(evidence_ids))),
            next_step,
        )

    @staticmethod
    def _hash(payload: Mapping) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest()
