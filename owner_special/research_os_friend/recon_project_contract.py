"""Project-creation contract for the bounded RECON governance boundary.

Protocol #10 is represented here as assurance depth, not as a task count.
The contract is declarative and side-effect free: RECON may validate project
identity, scope, invariants, recovery, evidence, and lifecycle, but it does not
grant authority to approve, merge, release, or bypass gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable

from .autobot_governance import GovernanceError

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_TEXT = 256
_MAX_ITEMS = 64


class AssuranceLevel(str, Enum):
    P0_IDENTITY = "P0"
    P1_FUNCTIONAL = "P1"
    P2_INTEGRATION = "P2"
    P3_REPRODUCIBILITY = "P3"
    P4_FORENSIC = "P4"
    P5_PROVENANCE = "P5"
    P6_GOVERNANCE = "P6"
    P7_ADVERSARIAL = "P7"
    P8_LIFECYCLE = "P8"
    P9_DISTRIBUTED = "P9"
    P10_CONTINUOUS = "P10"


class ProjectLifecycle(str, Enum):
    PROPOSED = "PROPOSED"
    DESIGNED = "DESIGNED"
    IMPLEMENTING = "IMPLEMENTING"
    VERIFYING = "VERIFYING"
    FORENSIC = "FORENSIC"
    REVIEW = "REVIEW"
    AUTHORIZED = "AUTHORIZED"
    RELEASED = "RELEASED"
    OPERATING = "OPERATING"
    REBASELINE = "REBASELINE"
    FAILED = "FAILED"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"
    RECOVERY = "RECOVERY"
    RETIRED = "RETIRED"


_FORBIDDEN_RECON_STATES = frozenset({
    ProjectLifecycle.AUTHORIZED,
    ProjectLifecycle.RELEASED,
})


@dataclass(frozen=True)
class ProjectCreationContract:
    """Minimal project DNA required before RECON treats a project as valid."""

    project_id: str
    project_name: str
    owner: str
    repository: str
    default_branch: str
    initial_commit: str
    protocol_version: str
    purpose: str
    boundary: str
    contract: str
    invariants: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    lifecycle: ProjectLifecycle = ProjectLifecycle.PROPOSED
    assurance_level: AssuranceLevel = AssuranceLevel.P0_IDENTITY
    recovery_defined: bool = False
    governance_defined: bool = False
    authority_defined: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("project_id", self.project_id),
            ("project_name", self.project_name),
            ("owner", self.owner),
            ("repository", self.repository),
            ("default_branch", self.default_branch),
            ("protocol_version", self.protocol_version),
            ("purpose", self.purpose),
            ("boundary", self.boundary),
            ("contract", self.contract),
        ):
            _bounded_text(value, name)
        if not _SHA_RE.fullmatch(self.initial_commit):
            raise GovernanceError("initial_commit must be a 40-character lowercase commit SHA")
        _bounded_items(self.invariants, "invariants")
        _bounded_items(self.evidence_requirements, "evidence_requirements")
        _bounded_items(self.dependencies, "dependencies")
        if self.lifecycle in _FORBIDDEN_RECON_STATES:
            raise GovernanceError("RECON cannot grant project authority or release state")
        if self.lifecycle == ProjectLifecycle.REBASELINE and not self.authority_defined:
            raise GovernanceError("rebaseline requires an explicit authority boundary")

    @property
    def identity_key(self) -> str:
        return f"{self.repository}@{self.initial_commit}"

    def validate_creation(self) -> tuple[str, ...]:
        """Return deterministic failures; UNKNOWN is never converted to PASS."""
        failures: list[str] = []
        if not self.invariants:
            failures.append("missing_invariants")
        if not self.evidence_requirements:
            failures.append("missing_evidence_requirements")
        if not self.recovery_defined:
            failures.append("missing_recovery")
        if not self.governance_defined:
            failures.append("missing_governance")
        if not self.authority_defined:
            failures.append("missing_authority_boundary")
        if self.assurance_level != AssuranceLevel.P0_IDENTITY and not self.contract:
            failures.append("missing_contract")
        return tuple(failures)

    def can_transition(self, target: ProjectLifecycle) -> bool:
        """Guard project lifecycle without allowing RECON to authorize release."""
        if not isinstance(target, ProjectLifecycle):
            raise GovernanceError("unknown project lifecycle")
        if target in _FORBIDDEN_RECON_STATES:
            return False
        if self.lifecycle in {ProjectLifecycle.FAILED, ProjectLifecycle.HOLD, ProjectLifecycle.BLOCKED}:
            return target == ProjectLifecycle.RECOVERY
        if self.lifecycle == ProjectLifecycle.RECOVERY:
            return target == ProjectLifecycle.VERIFYING
        if self.lifecycle == ProjectLifecycle.RETIRED:
            return False
        return target != self.lifecycle


def validate_project_creation(contract: ProjectCreationContract) -> tuple[str, ...]:
    if not isinstance(contract, ProjectCreationContract):
        raise GovernanceError("invalid project creation contract")
    return contract.validate_creation()


def _bounded_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TEXT:
        raise GovernanceError(f"{name} must be non-empty and bounded")


def _bounded_items(values: Iterable[str], name: str) -> None:
    values = tuple(values)
    if len(values) > _MAX_ITEMS:
        raise GovernanceError(f"{name} exceeds the bounded item limit")
    if any(not isinstance(item, str) or not item.strip() or len(item) > _MAX_TEXT for item in values):
        raise GovernanceError(f"{name} contains invalid items")
    if len(set(values)) != len(values):
        raise GovernanceError(f"{name} contains duplicates")
