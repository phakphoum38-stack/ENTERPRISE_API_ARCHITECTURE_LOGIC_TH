"""Deterministic durable-work graph primitives for AEOS.

This module is intentionally side-effect free: persistence, GitHub, and CI
adapters remain outside the graph boundary. The graph enforces lifecycle,
dependency, lease, baseline, and terminal-state invariants before mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple


class WorkGraphError(ValueError):
    """Raised when a work-graph invariant is violated."""


STATES = (
    "QUEUED",
    "READY",
    "LEASED",
    "RUNNING",
    "VERIFYING",
    "CERTIFYING",
    "COMPLETED",
    "BLOCKED",
    "QUARANTINED",
    "CANCELLED",
)
TERMINAL = frozenset({"COMPLETED", "BLOCKED", "QUARANTINED", "CANCELLED"})
MUTATING = frozenset({"LEASED", "RUNNING", "VERIFYING", "CERTIFYING"})


def _sha(value: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise WorkGraphError("baseline_sha must be a 40-character lowercase commit SHA")
    return value


@dataclass(frozen=True)
class WorkItem:
    work_id: str
    mission_id: str
    intent: str
    baseline_sha: str
    state: str = "QUEUED"
    risk: str = "LOW"
    dependencies: Tuple[str, ...] = ()
    lease_id: str | None = None
    attempt_count: int = 0
    evidence_refs: Tuple[str, ...] = ()
    failure_id: str | None = None
    recovery_state: str | None = None

    def __post_init__(self) -> None:
        if not self.work_id or not self.mission_id or not self.intent:
            raise WorkGraphError("work_id, mission_id, and intent are required")
        _sha(self.baseline_sha)
        if self.state not in STATES:
            raise WorkGraphError("invalid work state")
        if self.risk not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise WorkGraphError("invalid risk class")
        if type(self.attempt_count) is not int or self.attempt_count < 0:
            raise WorkGraphError("attempt_count must be a non-negative integer")
        if any(not isinstance(dep, str) or not dep for dep in self.dependencies):
            raise WorkGraphError("dependencies must contain non-empty work IDs")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise WorkGraphError("duplicate dependency")
        if self.work_id in self.dependencies:
            raise WorkGraphError("self dependency")
        if self.state in MUTATING and not self.lease_id:
            raise WorkGraphError("mutation state requires lease")
        if self.state in {"VERIFYING", "CERTIFYING", "COMPLETED"} and not self.evidence_refs:
            raise WorkGraphError("verification/certification requires evidence")
        if self.state == "COMPLETED" and self.failure_id:
            raise WorkGraphError("completed work cannot retain failure")


@dataclass
class WorkGraph:
    items: Dict[str, WorkItem] = field(default_factory=dict)

    def add(self, item: WorkItem) -> None:
        if item.work_id in self.items:
            raise WorkGraphError("duplicate work_id")
        for dependency in item.dependencies:
            if dependency == item.work_id:
                raise WorkGraphError("self dependency")
        self.items[item.work_id] = item
        try:
            self._assert_acyclic()
        except Exception:
            del self.items[item.work_id]
            raise

    def dependencies_satisfied(self, work_id: str) -> bool:
        item = self._get(work_id)
        return all(self.items.get(dep) is not None and self.items[dep].state == "COMPLETED" for dep in item.dependencies)

    def ready(self) -> Tuple[str, ...]:
        return tuple(sorted(item.work_id for item in self.items.values() if item.state == "QUEUED" and self.dependencies_satisfied(item.work_id)))

    def transition(self, work_id: str, new_state: str, *, observed_sha: str | None = None, lease_id: str | None = None, evidence_refs: Iterable[str] = ()) -> WorkItem:
        item = self._get(work_id)
        if new_state not in STATES:
            raise WorkGraphError("invalid target state")
        if item.state in TERMINAL:
            raise WorkGraphError("terminal work item is immutable")
        if new_state in MUTATING:
            if not lease_id or lease_id != item.lease_id:
                raise WorkGraphError("exact lease required for mutation")
            if observed_sha != item.baseline_sha:
                raise WorkGraphError("observed SHA must exactly match baseline")
        refs = tuple(evidence_refs)
        if new_state in {"VERIFYING", "CERTIFYING", "COMPLETED"} and not refs and not item.evidence_refs:
            raise WorkGraphError("evidence required before verification/certification")
        updated = WorkItem(
            work_id=item.work_id, mission_id=item.mission_id, intent=item.intent,
            baseline_sha=item.baseline_sha, state=new_state, risk=item.risk,
            dependencies=item.dependencies, lease_id=item.lease_id,
            attempt_count=item.attempt_count, evidence_refs=refs or item.evidence_refs,
            failure_id=item.failure_id, recovery_state=item.recovery_state,
        )
        self.items[work_id] = updated
        return updated

    def _get(self, work_id: str) -> WorkItem:
        if work_id not in self.items:
            raise WorkGraphError("unknown work_id")
        return self.items[work_id]

    def _assert_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting:
                raise WorkGraphError("dependency cycle")
            if node in visited:
                return
            visiting.add(node)
            for dep in self.items[node].dependencies:
                if dep in self.items:
                    visit(dep)
            visiting.remove(node)
            visited.add(node)
        for node in self.items:
            visit(node)
