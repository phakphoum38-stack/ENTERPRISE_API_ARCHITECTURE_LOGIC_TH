from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .factory import MasterOrchestrator, VersionFactory
from .hierarchy import AdaptiveHierarchyPlanner, HierarchyPlan


@dataclass(frozen=True)
class WorkAssignment:
    version: str
    factory_namespace: str
    orchestrator_node: str


@dataclass(frozen=True)
class EvidenceRecord:
    timestamp: str
    version: str
    action: str
    detail: str


@dataclass
class EvidenceLedger:
    records: list[EvidenceRecord] = field(default_factory=list)

    def append(self, version: str, action: str, detail: str) -> EvidenceRecord:
        record = EvidenceRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=version,
            action=action,
            detail=detail,
        )
        self.records.append(record)
        return record


class ConflictCoordinator:
    """Simple in-memory write lease manager for version-isolated factories."""

    def __init__(self) -> None:
        self._leases: dict[Path, str] = {}

    def acquire(self, version: str, target: Path) -> None:
        target = target.resolve()
        owner = self._leases.get(target)
        if owner is not None and owner != version:
            raise RuntimeError(f"target {target} is already leased by factory {owner}")
        self._leases[target] = version

    def release(self, version: str, target: Path) -> None:
        target = target.resolve()
        owner = self._leases.get(target)
        if owner == version:
            self._leases.pop(target, None)


@dataclass
class AdaptiveControlPlane:
    repository_root: Path
    planner: AdaptiveHierarchyPlanner = field(default_factory=AdaptiveHierarchyPlanner)
    ledger: EvidenceLedger = field(default_factory=EvidenceLedger)
    conflicts: ConflictCoordinator = field(default_factory=ConflictCoordinator)

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        self.master = MasterOrchestrator(self.repository_root)
        self._plan: HierarchyPlan | None = None
        self._assignments: dict[str, WorkAssignment] = {}

    @property
    def plan_state(self) -> HierarchyPlan | None:
        return self._plan

    def configure_versions(self, versions: Iterable[str]) -> HierarchyPlan:
        plan = self.planner.plan(versions)
        self._plan = plan
        self._assignments.clear()

        leaf_nodes = [node for node in plan.root.walk() if node.assigned_versions]
        for node in leaf_nodes:
            for version in node.assigned_versions:
                factory = self.master.register_version(version, branch=f"version/{version}")
                assignment = WorkAssignment(
                    version=version,
                    factory_namespace=factory.namespace,
                    orchestrator_node=node.node_id,
                )
                self._assignments[version] = assignment
                self.ledger.append(
                    version,
                    "factory_registered",
                    f"assigned to {node.node_id} under profile {plan.profile.label}",
                )
        return plan

    def assignment_for(self, version: str) -> WorkAssignment:
        try:
            return self._assignments[version]
        except KeyError as exc:
            raise KeyError(f"version {version!r} has no active factory assignment") from exc

    def factory_for(self, version: str) -> VersionFactory:
        return self.master.get_factory(version)

    def begin_write(self, version: str, target: Path) -> None:
        self.master.assert_isolated_target(version, target)
        self.conflicts.acquire(version, target)
        self.ledger.append(version, "write_lease_acquired", str(target.resolve()))

    def end_write(self, version: str, target: Path) -> None:
        self.conflicts.release(version, target)
        self.ledger.append(version, "write_lease_released", str(target.resolve()))

    def summary(self) -> dict[str, object]:
        if self._plan is None:
            return {
                "configured": False,
                "active_factories": 0,
                "active_orchestrators": 0,
                "profile": None,
            }
        return {
            "configured": True,
            "active_factories": self._plan.active_factories,
            "active_orchestrators": self._plan.active_orchestrators,
            "profile": self._plan.profile.label,
            "logical_capacity": self._plan.profile.capacity,
            "versions": tuple(self._assignments),
        }
