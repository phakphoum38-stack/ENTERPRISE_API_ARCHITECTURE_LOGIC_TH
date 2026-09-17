"""P0-10 continuous assurance boundary for the bounded project fleet.

This module is a side-effect-free assurance projection. It validates the
existing fleet, concurrency metadata, coordination fencing, and supervisor
decision projections without scheduling, executing, repairing, authorizing,
merging, or changing Git state.

Unknown or missing assurance inputs fail closed; assurance never grants
authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .continuous_supervisor import ACTIONS, SupervisorDecision
from .distributed_coordination import ConcurrentProject, CoordinationClaim, DistributedCoordinationError
from .project_fleet import MAX_PROJECTS, ProjectFleet, ProjectFleetError


class ContinuousAssuranceError(CanonicalIdentityError):
    """Raised when a fleet assurance invariant cannot be established."""


@dataclass(frozen=True)
class FleetAssuranceObservation:
    """Immutable evidence projection for one fleet member."""

    project_id: str
    identity: CanonicalIdentity
    supervisor_action: str
    concurrency_active: int
    concurrency_limit: int
    claim_epoch: int | None
    claim_active: bool | None
    claim_fenced: bool
    evidence_complete: bool = True

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ContinuousAssuranceError("project_id is required")
        if self.supervisor_action not in ACTIONS:
            raise ContinuousAssuranceError(
                f"unknown supervisor action: {self.supervisor_action}"
            )
        if self.concurrency_limit < 1:
            raise ContinuousAssuranceError("concurrency_limit must be >= 1")
        if self.concurrency_active < 0 or self.concurrency_active > self.concurrency_limit:
            raise ContinuousAssuranceError("concurrency exceeds project bound")
        if not self.evidence_complete:
            raise ContinuousAssuranceError("assurance evidence is incomplete")
        if self.claim_epoch is None and (self.claim_active is not None or self.claim_fenced):
            raise ContinuousAssuranceError("claim fencing metadata is incomplete")
        if self.claim_epoch is not None and self.claim_epoch < 1:
            raise ContinuousAssuranceError("claim_epoch must be >= 1")

    def fingerprint(self) -> str:
        material = {
            "project_id": self.project_id,
            "identity": self.identity.as_mapping(),
            "supervisor_action": self.supervisor_action,
            "concurrency_active": self.concurrency_active,
            "concurrency_limit": self.concurrency_limit,
            "claim_epoch": self.claim_epoch,
            "claim_active": self.claim_active,
            "claim_fenced": self.claim_fenced,
            "evidence_complete": self.evidence_complete,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class FleetAssuranceSummary:
    """Immutable fleet-wide assurance result.

    PASS means the supplied assurance inputs are complete and internally
    consistent. HOLD means assurance cannot establish PASS; it never means
    authority to continue execution.
    """

    status: str
    project_count: int
    capacity: int
    observations: tuple[FleetAssuranceObservation, ...]
    decision_fingerprints: tuple[str, ...]
    assurance_fingerprint: str
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"PASS", "HOLD"}:
            raise ContinuousAssuranceError("invalid assurance status")
        if self.project_count != len(self.observations):
            raise ContinuousAssuranceError("project_count mismatch")
        if self.project_count > self.capacity:
            raise ContinuousAssuranceError("project count exceeds capacity")

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    @property
    def blocked(self) -> bool:
        return self.status == "HOLD"


def _decision_fingerprint(decision: SupervisorDecision) -> str:
    material = {
        "action": decision.action,
        "identity": decision.identity.as_mapping(),
        "reason": decision.reason,
        "requires_new_attempt": decision.requires_new_attempt,
        "preserves_evidence": decision.preserves_evidence,
    }
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def observe_project(
    *,
    fleet: ProjectFleet,
    project: ConcurrentProject,
    claim: CoordinationClaim | None = None,
    expected_epoch: int | None = None,
    decision: SupervisorDecision | None = None,
) -> FleetAssuranceObservation:
    """Build one assurance observation from existing authoritative records."""

    try:
        registered = fleet.get(project.project_id)
    except ProjectFleetError as exc:
        raise ContinuousAssuranceError(str(exc)) from exc

    if registered.identity != project.identity:
        raise ContinuousAssuranceError("fleet/project canonical identity mismatch")

    if decision is not None and decision.identity != project.identity:
        raise ContinuousAssuranceError("supervisor decision identity mismatch")
    action = decision.action if decision is not None else registered.supervisor_action
    if action not in ACTIONS:
        raise ContinuousAssuranceError("unknown supervisor action")

    if claim is None:
        if expected_epoch is not None:
            raise ContinuousAssuranceError("expected_epoch requires coordination claim")
        return FleetAssuranceObservation(
            project_id=project.project_id,
            identity=project.identity,
            supervisor_action=action,
            concurrency_active=project.active_units,
            concurrency_limit=project.max_parallel_units,
            claim_epoch=None,
            claim_active=None,
            claim_fenced=False,
        )

    if expected_epoch is None:
        raise ContinuousAssuranceError("coordination claim requires expected_epoch")
    if claim.project_id != project.project_id or claim.identity != project.identity:
        raise ContinuousAssuranceError("coordination claim identity mismatch")
    if not claim.fenced(epoch=expected_epoch):
        raise ContinuousAssuranceError("stale or inactive coordination claim")

    return FleetAssuranceObservation(
        project_id=project.project_id,
        identity=project.identity,
        supervisor_action=action,
        concurrency_active=project.active_units,
        concurrency_limit=project.max_parallel_units,
        claim_epoch=claim.epoch,
        claim_active=claim.active,
        claim_fenced=True,
    )


def _assert_unique(observations: tuple[FleetAssuranceObservation, ...]) -> None:
    project_ids = [item.project_id for item in observations]
    work_ids = [item.identity.work_id for item in observations]
    mission_ids = [item.identity.mission_id for item in observations]
    if len(project_ids) != len(set(project_ids)):
        raise ContinuousAssuranceError("duplicate project_id in assurance set")
    if len(work_ids) != len(set(work_ids)):
        raise ContinuousAssuranceError("duplicate canonical work_id in assurance set")
    if len(mission_ids) != len(set(mission_ids)):
        raise ContinuousAssuranceError("duplicate canonical mission_id in assurance set")


def assure_fleet(
    *,
    fleet: ProjectFleet,
    observations: Iterable[FleetAssuranceObservation],
    decisions: Iterable[SupervisorDecision] = (),
) -> FleetAssuranceSummary:
    """Return a deterministic fleet assurance projection.

    The function never applies a supervisor action. It only validates the
    bounded assurance inputs supplied by existing execution/governance planes.
    """

    items = tuple(observations)
    if len(items) != fleet.size:
        raise ContinuousAssuranceError("assurance coverage does not match fleet size")
    _assert_unique(items)

    for item in items:
        registered = fleet.get(item.project_id)
        if registered.identity != item.identity:
            raise ContinuousAssuranceError("assurance identity mismatch")
        if item.concurrency_active > item.concurrency_limit:
            raise ContinuousAssuranceError("concurrency bound violated")
        if item.claim_epoch is not None and not item.claim_fenced:
            raise ContinuousAssuranceError("unfenced claim cannot establish assurance")

    decision_items = tuple(decisions)
    for decision in decision_items:
        if decision.action not in ACTIONS:
            raise ContinuousAssuranceError("unknown supervisor action")
        if not any(item.identity == decision.identity for item in items):
            raise ContinuousAssuranceError("decision identity absent from assurance set")

    reasons: list[str] = []
    for item in items:
        if item.supervisor_action == "QUARANTINE":
            reasons.append(f"{item.project_id}: quarantine decision requires isolation")
        if item.supervisor_action in {"RETRY", "RECOVER", "RESCAN"}:
            reasons.append(
                f"{item.project_id}: {item.supervisor_action} is an active assurance condition"
            )

    status = "HOLD" if reasons else "PASS"
    decision_fingerprints = tuple(_decision_fingerprint(item) for item in decision_items)
    material = {
        "status": status,
        "project_count": len(items),
        "capacity": MAX_PROJECTS,
        "observations": [item.fingerprint() for item in items],
        "decision_fingerprints": list(decision_fingerprints),
        "reasons": reasons,
    }
    assurance_fingerprint = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return FleetAssuranceSummary(
        status=status,
        project_count=len(items),
        capacity=MAX_PROJECTS,
        observations=items,
        decision_fingerprints=decision_fingerprints,
        assurance_fingerprint=assurance_fingerprint,
        reasons=tuple(reasons),
    )
