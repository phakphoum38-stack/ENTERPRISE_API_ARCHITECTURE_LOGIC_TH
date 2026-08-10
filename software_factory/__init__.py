"""Adaptive Hierarchical AI Software Factory primitives."""

from .control_plane import (
    AdaptiveControlPlane,
    ConflictCoordinator,
    EvidenceLedger,
    EvidenceRecord,
    WorkAssignment,
)
from .factory import AgentRole, FactoryAgent, MasterOrchestrator, VersionFactory
from .hierarchy import (
    AdaptiveHierarchyPlanner,
    HierarchyPlan,
    OrchestratorNode,
    PowerProfile,
    SUPPORTED_PROFILES,
)

__all__ = [
    "AdaptiveControlPlane",
    "AdaptiveHierarchyPlanner",
    "AgentRole",
    "ConflictCoordinator",
    "EvidenceLedger",
    "EvidenceRecord",
    "FactoryAgent",
    "HierarchyPlan",
    "MasterOrchestrator",
    "OrchestratorNode",
    "PowerProfile",
    "SUPPORTED_PROFILES",
    "VersionFactory",
    "WorkAssignment",
]
