"""P0-8 bounded fleet federation for up to 100 concurrent projects.

The fleet is a declarative registry. It does not schedule, enqueue, execute,
lease, retry, or mutate any existing execution plane. Existing Scheduler,
AEOS, queues, workers, and state machines remain authoritative.

The fleet only binds project descriptors to canonical identity and exposes
bounded supervisor decision projections.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .continuous_supervisor import SupervisorDecision


class ProjectFleetError(CanonicalIdentityError):
    """Raised when a bounded fleet invariant is violated."""


MAX_PROJECTS = 100


@dataclass(frozen=True)
class FleetProject:
    """Immutable descriptor for one project in the bounded fleet."""

    project_id: str
    identity: CanonicalIdentity
    state: str = "ACTIVE"
    supervisor_action: str = "NOOP"

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ProjectFleetError("project_id must be a non-empty string")
        if not isinstance(self.state, str) or not self.state.strip():
            raise ProjectFleetError("state must be a non-empty string")
        if not isinstance(self.supervisor_action, str) or not self.supervisor_action.strip():
            raise ProjectFleetError("supervisor_action must be a non-empty string")

    def with_supervisor_decision(self, decision: SupervisorDecision) -> "FleetProject":
        """Return a new descriptor after recording an existing supervisor decision."""
        if decision.identity != self.identity:
            raise ProjectFleetError("supervisor decision identity mismatch")
        return replace(self, supervisor_action=decision.action)

    def fingerprint(self) -> str:
        """Return deterministic identity for the project descriptor."""
        import hashlib
        material = (
            self.project_id,
            self.identity.fingerprint(),
            self.state,
            self.supervisor_action,
        )
        return hashlib.sha256("|".join(material).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProjectFleet:
    """Immutable bounded registry for at most 100 concurrent projects."""

    projects: tuple[FleetProject, ...] = ()

    def __post_init__(self) -> None:
        if len(self.projects) > MAX_PROJECTS:
            raise ProjectFleetError(f"fleet capacity exceeded: max {MAX_PROJECTS} projects")
        project_ids = [p.project_id for p in self.projects]
        if len(project_ids) != len(set(project_ids)):
            raise ProjectFleetError("duplicate project_id")
        work_ids = [p.identity.work_id for p in self.projects]
        if len(work_ids) != len(set(work_ids)):
            raise ProjectFleetError("duplicate canonical work_id")
        mission_ids = [p.identity.mission_id for p in self.projects]
        if len(mission_ids) != len(set(mission_ids)):
            raise ProjectFleetError("duplicate canonical mission_id")

    @property
    def capacity(self) -> int:
        return MAX_PROJECTS

    @property
    def size(self) -> int:
        return len(self.projects)

    @property
    def remaining(self) -> int:
        return MAX_PROJECTS - len(self.projects)

    def register(self, project: FleetProject) -> "ProjectFleet":
        """Return a new fleet containing project; never schedules or executes it."""
        if self.size >= MAX_PROJECTS:
            raise ProjectFleetError(f"fleet capacity exceeded: max {MAX_PROJECTS} projects")
        if any(existing.project_id == project.project_id for existing in self.projects):
            raise ProjectFleetError("duplicate project_id")
        if any(existing.identity.work_id == project.identity.work_id for existing in self.projects):
            raise ProjectFleetError("duplicate canonical work_id")
        if any(existing.identity.mission_id == project.identity.mission_id for existing in self.projects):
            raise ProjectFleetError("duplicate canonical mission_id")
        return ProjectFleet(self.projects + (project,))

    def replace(self, project: FleetProject) -> "ProjectFleet":
        """Return a new fleet with one descriptor replaced by project."""
        matches = [p for p in self.projects if p.project_id == project.project_id]
        if len(matches) != 1:
            raise ProjectFleetError("project_id not registered")
        retained = tuple(p for p in self.projects if p.project_id != project.project_id)
        return ProjectFleet(retained + (project,))

    def remove(self, project_id: str) -> "ProjectFleet":
        """Return a new fleet without a project descriptor."""
        retained = tuple(p for p in self.projects if p.project_id != project_id)
        if len(retained) == len(self.projects):
            raise ProjectFleetError("project_id not registered")
        return ProjectFleet(retained)

    def get(self, project_id: str) -> FleetProject:
        for project in self.projects:
            if project.project_id == project_id:
                return project
        raise ProjectFleetError("project_id not registered")

    def with_decision(self, decision: SupervisorDecision) -> "ProjectFleet":
        """Record a supervisor decision without applying its execution action."""
        project = next(
            (p for p in self.projects if p.identity == decision.identity),
            None,
        )
        if project is None:
            raise ProjectFleetError("canonical identity not registered in fleet")
        return self.replace(project.with_supervisor_decision(decision))


def build_fleet(projects: Iterable[FleetProject] = ()) -> ProjectFleet:
    """Build a bounded fleet from existing immutable project descriptors."""
    return ProjectFleet(tuple(projects))
