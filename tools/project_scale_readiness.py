"""Deterministic 100-project readiness harness using the existing shared-core model."""
from __future__ import annotations
from dataclasses import dataclass

from tools.project_registry import (
    FINAL_GATE,
    SHARED_CAPABILITY_REGISTRY,
    SHARED_EVIDENCE_LEDGER,
    SHARED_QUEUE,
    ProjectDefinition,
    ProjectRegistry,
)

PROJECT_COUNT = 100

@dataclass(frozen=True)
class ProjectContext:
    project_id: str
    capability_namespace: str
    queue_namespace: str
    evidence_namespace: str
    final_gate: str = "FINAL_GATE"

def build_project_contexts(count: int = PROJECT_COUNT) -> tuple[ProjectContext, ...]:
    if count != PROJECT_COUNT:
        raise ValueError("readiness harness is defined for exactly 100 projects")
    return tuple(
        ProjectContext(
            project_id=f"project-{index:03d}",
            capability_namespace="SHARED_CAPABILITY_REGISTRY",
            queue_namespace="SHARED_QUEUE",
            evidence_namespace="SHARED_EVIDENCE_LEDGER",
        )
        for index in range(1, count + 1)
    )

def validate_project_contexts(contexts: tuple[ProjectContext, ...]) -> tuple[str, ...]:
    errors: list[str] = []
    if len(contexts) != PROJECT_COUNT:
        errors.append("project count is not 100")
    project_ids = [item.project_id for item in contexts]
    if len(set(project_ids)) != len(project_ids):
        errors.append("duplicate project identity")
    if any(not item.project_id for item in contexts):
        errors.append("missing project identity")
    if any(item.capability_namespace != "SHARED_CAPABILITY_REGISTRY" for item in contexts):
        errors.append("capability registry is not shared")
    if any(item.queue_namespace != "SHARED_QUEUE" for item in contexts):
        errors.append("queue is not shared")
    if any(item.evidence_namespace != "SHARED_EVIDENCE_LEDGER" for item in contexts):
        errors.append("evidence ledger is not shared")
    if any(item.final_gate != "FINAL_GATE" for item in contexts):
        errors.append("second final gate detected")
    return tuple(errors)

def build_idempotency_key(*, project_id: str, event_id: str, source_sha: str, action: str) -> str:
    if not all((project_id, event_id, source_sha, action)):
        raise ValueError("idempotency identity is incomplete")
    return "|".join((project_id, event_id, source_sha, action))

def validate_isolation(*, project_a: ProjectContext, project_b: ProjectContext) -> tuple[str, ...]:
    errors: list[str] = []
    if project_a.project_id == project_b.project_id:
        errors.append("project identities collide")
    if build_idempotency_key(project_id=project_a.project_id,event_id="event-1",source_sha="a"*40,action="execute") == build_idempotency_key(project_id=project_b.project_id,event_id="event-1",source_sha="a"*40,action="execute"):
        errors.append("idempotency crosses project boundary")
    return tuple(errors)


def build_project_definitions(count: int = PROJECT_COUNT) -> tuple[ProjectDefinition, ...]:
    if not 1 <= count <= PROJECT_COUNT:
        raise ValueError("project count must be between 1 and 100")
    capabilities = (
        "control_center",
        "friend",
        "agent",
        "github",
        "factory_v3",
        "assurance",
    )
    return tuple(
        ProjectDefinition(
            project_id=f"project-{index:03d}",
            display_name=f"Research OS Project {index:03d}",
            version="1.0.0",
            capabilities=capabilities,
            authorization_policy="EXISTING_AUTHORIZATION_BOUNDARY",
            workflow_profile="SHARED_WORKFLOW",
            evidence_namespace=f"PROJECT:project-{index:03d}",
            resource_policy="REJECT_ON_CONFLICT",
            capability_namespace=SHARED_CAPABILITY_REGISTRY,
            queue_namespace=SHARED_QUEUE,
            evidence_ledger=SHARED_EVIDENCE_LEDGER,
            release_authority=FINAL_GATE,
        )
        for index in range(1, count + 1)
    )


SCALE_LEVELS = (10, 20, 50, 100)

def validate_registry_scale(count: int = PROJECT_COUNT) -> tuple[str, ...]:
    registry = ProjectRegistry(build_project_definitions(count))
    projects = registry.all()
    errors = []
    if len(projects) != count:
        errors.append("registry did not retain all project definitions")
    project_ids = [project.project_id for project in projects]
    if len(project_ids) != len(set(project_ids)):
        errors.append("registry contains duplicate project identity")
    for project in projects:
        if project.evidence_namespace != f"PROJECT:{project.project_id}":
            errors.append(f"{project.project_id}: evidence namespace mismatch")
    return tuple(errors)


def validate_scale_levels() -> tuple[str, ...]:
    errors: list[str] = []
    for count in SCALE_LEVELS:
        errors.extend(
            f"{count}: {error}" for error in validate_registry_scale(count)
        )
    return tuple(errors)
