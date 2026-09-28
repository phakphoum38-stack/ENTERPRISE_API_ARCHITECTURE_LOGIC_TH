"""Canonical project configuration registry for the shared Research OS core.

Project definitions are configuration, not a second execution authority.
Execution, authorization, evidence, queueing, and release remain owned by the
existing platform components.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tools.control_center_capability_registry import get_capability


SHARED_CAPABILITY_REGISTRY = "SHARED_CAPABILITY_REGISTRY"
SHARED_QUEUE = "SHARED_QUEUE"
SHARED_EVIDENCE_LEDGER = "SHARED_EVIDENCE_LEDGER"
FINAL_GATE = "FINAL_GATE"


@dataclass(frozen=True)
class ProjectDefinition:
    project_id: str
    display_name: str
    version: str
    capabilities: tuple[str, ...]
    authorization_policy: str
    workflow_profile: str
    evidence_namespace: str
    resource_policy: str
    capability_namespace: str = SHARED_CAPABILITY_REGISTRY
    queue_namespace: str = SHARED_QUEUE
    evidence_ledger: str = SHARED_EVIDENCE_LEDGER
    release_authority: str = FINAL_GATE

    def __post_init__(self) -> None:
        values = (
            ("project_id", self.project_id),
            ("display_name", self.display_name),
            ("version", self.version),
            ("authorization_policy", self.authorization_policy),
            ("workflow_profile", self.workflow_profile),
            ("evidence_namespace", self.evidence_namespace),
            ("resource_policy", self.resource_policy),
        )
        for name, value in values:
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.capabilities:
            raise ValueError("at least one capability is required")
        if self.capability_namespace != SHARED_CAPABILITY_REGISTRY:
            raise ValueError("project-specific capability registry is forbidden")
        if self.queue_namespace != SHARED_QUEUE:
            raise ValueError("project-specific queue is forbidden")
        if self.evidence_ledger != SHARED_EVIDENCE_LEDGER:
            raise ValueError("project-specific evidence ledger is forbidden")
        if self.release_authority != FINAL_GATE:
            raise ValueError("second release authority is forbidden")


class ProjectRegistry:
    """Immutable-in-use registry facade over project definitions."""

    def __init__(self, projects: Iterable[ProjectDefinition] = ()) -> None:
        self._projects: dict[str, ProjectDefinition] = {}
        for project in projects:
            self.register(project)

    def register(self, project: ProjectDefinition) -> ProjectDefinition:
        if project.project_id in self._projects:
            raise ValueError(f"duplicate project_id: {project.project_id}")
        for capability_id in project.capabilities:
            get_capability(capability_id)
        if project.evidence_namespace != f"PROJECT:{project.project_id}":
            raise ValueError("evidence namespace must bind to project identity")
        self._projects[project.project_id] = project
        return project

    def get(self, project_id: str) -> ProjectDefinition:
        if not project_id.strip():
            raise ValueError("project_id is required")
        try:
            return self._projects[project_id]
        except KeyError as exc:
            raise KeyError(f"unknown project_id: {project_id}") from exc

    def all(self) -> tuple[ProjectDefinition, ...]:
        return tuple(self._projects.values())

    def build_idempotency_key(
        self,
        *,
        project_id: str,
        event_id: str,
        source_sha: str,
        action: str,
    ) -> str:
        project = self.get(project_id)
        if not all((event_id, source_sha, action)):
            raise ValueError("idempotency identity is incomplete")
        return "|".join((project.project_id, event_id, source_sha, action))


def validate_registry(
    projects: Iterable[ProjectDefinition],
) -> tuple[str, ...]:
    items = tuple(projects)
    errors: list[str] = []
    ids = [item.project_id for item in items]
    if len(ids) != len(set(ids)):
        errors.append("duplicate project identity")
    for project in items:
        try:
            for capability_id in project.capabilities:
                get_capability(capability_id)
        except KeyError as exc:
            errors.append(str(exc))
        if project.evidence_namespace != f"PROJECT:{project.project_id}":
            errors.append(f"{project.project_id}: evidence namespace mismatch")
        if project.capability_namespace != SHARED_CAPABILITY_REGISTRY:
            errors.append(f"{project.project_id}: capability registry is not shared")
        if project.queue_namespace != SHARED_QUEUE:
            errors.append(f"{project.project_id}: queue is not shared")
        if project.evidence_ledger != SHARED_EVIDENCE_LEDGER:
            errors.append(f"{project.project_id}: evidence ledger is not shared")
        if project.release_authority != FINAL_GATE:
            errors.append(f"{project.project_id}: second final gate detected")
    return tuple(errors)


PROJECT_001 = ProjectDefinition(
    project_id="project-001",
    display_name="Research OS Reference Project",
    version="1.0.0",
    capabilities=(
        "control_center",
        "friend",
        "agent",
        "github",
        "factory_v3",
        "assurance",
    ),
    authorization_policy="EXISTING_AUTHORIZATION_BOUNDARY",
    workflow_profile="SHARED_WORKFLOW",
    evidence_namespace="PROJECT:project-001",
    resource_policy="REJECT_ON_CONFLICT",
)


__all__ = [
    "FINAL_GATE",
    "PROJECT_001",
    "ProjectDefinition",
    "ProjectRegistry",
    "SHARED_CAPABILITY_REGISTRY",
    "SHARED_EVIDENCE_LEDGER",
    "SHARED_QUEUE",
    "validate_registry",
]
