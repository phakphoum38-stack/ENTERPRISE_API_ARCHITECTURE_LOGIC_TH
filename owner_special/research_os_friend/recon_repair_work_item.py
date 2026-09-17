"""P0-4 bridge: convert a bounded RECON RepairSet into an AEOS WorkItem.

This is an adapter only. It does not enqueue, lease, execute, repair, merge,
or grant authority. Existing AEOS WorkItem remains the canonical repair-work
container.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable

from .aeos_durable_work_graph import WorkItem
from .recon_failure import ReconFailure
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError


class ReconRepairMappingError(CanonicalIdentityError):
    """Raised when a RECON repair cannot be converted safely to AEOS work."""


@dataclass(frozen=True)
class RepairSetView:
    """Structural view of the existing H00-H27 RepairSet contract."""

    root_causes: tuple[str, ...]
    intents: tuple[str, ...]
    changed_files: tuple[str, ...]
    regression_tests: tuple[str, ...]
    fingerprint: str


def _tuple_text(values: Iterable[str], name: str) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(not isinstance(v, str) or not v.strip() for v in result):
        raise ReconRepairMappingError(f"{name} must contain non-empty strings")
    if len(set(result)) != len(result):
        raise ReconRepairMappingError(f"{name} contains duplicates")
    return tuple(v.strip() for v in result)


def repair_set_view(repair_set: Any) -> RepairSetView:
    values = RepairSetView(
        root_causes=_tuple_text(repair_set.root_causes, "root_causes"),
        intents=_tuple_text(repair_set.intents, "intents"),
        changed_files=_tuple_text(repair_set.changed_files, "changed_files"),
        regression_tests=_tuple_text(repair_set.regression_tests, "regression_tests"),
        fingerprint=repair_set.fingerprint,
    )
    if not isinstance(values.fingerprint, str) or len(values.fingerprint) != 64:
        raise ReconRepairMappingError("repair_set fingerprint must be SHA-256")
    return values


def _work_id(identity: CanonicalIdentity, failure: ReconFailure, repair: RepairSetView) -> str:
    material = {
        "mission_id": identity.mission_id,
        "work_id": identity.work_id,
        "baseline_sha": identity.baseline_sha,
        "failure_fingerprint": failure.fingerprint,
        "repair_set_fingerprint": repair.fingerprint,
    }
    return "recon-repair-" + hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:32]


def build_repair_work_item(
    *,
    identity: CanonicalIdentity,
    failure: ReconFailure,
    repair_set: Any,
    mission_id: str | None = None,
    dependencies: Iterable[str] = (),
    risk: str = "HIGH",
) -> WorkItem:
    """Create one deterministic AEOS WorkItem from RECON evidence.

    The returned item starts in QUEUED and has no lease, attempt, execution,
    or authority. The original identity/work lineage and exact baseline SHA
    are preserved.
    """

    repair = repair_set_view(repair_set)
    if failure.source_sha != identity.baseline_sha:
        raise ReconRepairMappingError("RECON failure source SHA does not match canonical baseline")
    if mission_id is not None and mission_id != identity.mission_id:
        raise ReconRepairMappingError("mission_id does not match canonical identity")
    if not failure.fingerprint:
        raise ReconRepairMappingError("RECON failure fingerprint is required")

    dependency_ids = tuple(dependencies)
    if len(set(dependency_ids)) != len(dependency_ids):
        raise ReconRepairMappingError("duplicate repair dependency")
    if identity.work_id in dependency_ids:
        raise ReconRepairMappingError("repair work cannot depend on itself")

    intent_payload = {
        "type": "RECON_REPAIR",
        "failure_fingerprint": failure.fingerprint,
        "failure_kind": failure.kind.value,
        "gate": failure.gate,
        "test": failure.test,
        "root_causes": repair.root_causes,
        "repair_intents": repair.intents,
        "changed_files": repair.changed_files,
        "regression_tests": repair.regression_tests,
        "repair_set_fingerprint": repair.fingerprint,
    }
    intent = json.dumps(intent_payload, sort_keys=True, separators=(",", ":"))

    return WorkItem(
        work_id=_work_id(identity, failure, repair),
        mission_id=identity.mission_id,
        intent=intent,
        baseline_sha=identity.baseline_sha,
        state="QUEUED",
        risk=risk,
        dependencies=dependency_ids,
        attempt_count=0,
        evidence_refs=(failure.fingerprint, repair.fingerprint),
        failure_id=failure.fingerprint,
        recovery_state="RECON_REPAIR_PLANNED",
    )
