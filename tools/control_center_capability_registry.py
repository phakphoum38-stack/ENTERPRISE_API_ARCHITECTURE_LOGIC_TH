"""Canonical, read-only capability binding registry for the Control Center.

This module is deliberately declarative. It does not execute Friend, Agent,
GitHub, Factory/V3, or Assurance work. Its job is to give the central control
plane one canonical vocabulary for locating existing engines and identifying
which lifecycle links are still missing.

The registry prevents the Control Center from becoming a second runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


STATUSES = frozenset({
    "CANONICAL_WIRED",
    "IMPLEMENTED_NOT_WIRED",
    "WIRED_NOT_EXECUTABLE",
    "MISSING_EXECUTOR",
    "PARTIAL",
    "ORPHAN",
    "DUPLICATE",
    "UNKNOWN",
})


@dataclass(frozen=True)
class CapabilityBinding:
    capability_id: str
    domain: str
    label: str
    ui_ref: str
    contract_ref: str
    runtime_ref: str
    executor_ref: str
    observation_ref: str
    evidence_ref: str
    state_ref: str
    inspector_ref: str
    status: str
    notes: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("capability_id", self.capability_id),
            ("domain", self.domain),
            ("label", self.label),
            ("ui_ref", self.ui_ref),
            ("contract_ref", self.contract_ref),
            ("runtime_ref", self.runtime_ref),
            ("executor_ref", self.executor_ref),
            ("observation_ref", self.observation_ref),
            ("evidence_ref", self.evidence_ref),
            ("state_ref", self.state_ref),
            ("inspector_ref", self.inspector_ref),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.status not in STATUSES:
            raise ValueError(f"unsupported status: {self.status}")


# Evidence basis: paths/classes below are present on the canonical main
# snapshot 410c05fac73744495c55a17ba822156b3b68a09b. "PARTIAL" is intentional:
# it means the component exists, but the full central lifecycle is not yet
# proven as one executable binding on that snapshot.
CANONICAL_CAPABILITY_BINDINGS: tuple[CapabilityBinding, ...] = (
    CapabilityBinding(
        "control_center",
        "CONTROL",
        "Native Control Center",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart",
        "current/NATIVE_CONTROL_CENTER_OPERATING_CONTRACT.json",
        "tools/native_control_center.py:ControlCommand",
        "tools/native_control_center.py:NativeControlCenter",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_Activity",
        "current/NATIVE_CONTROL_CENTER_OPERATING_CONTRACT.json",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_StateView",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_Inspector",
        "CANONICAL_WIRED",
        "Central control surface exists; execution remains delegated to existing engines.",
    ),
    CapabilityBinding(
        "friend",
        "FRIEND",
        "Friend Runtime",
        "apps/research_os_flutter/lib/src/features/chat/chat_page.dart",
        "current/OWNER_MANIFEST.json",
        "owner_special/research_os_friend/runtime.py:FriendRuntime",
        "owner_special/research_os_friend/orchestrator.py:FriendOrchestrator",
        "owner_special/research_os_friend/runtime.py:EvidenceRecorder",
        "owner_special/research_os_friend/runtime.py:EvidenceRecorder",
        "owner_special/research_os_friend/runtime.py:FriendRuntime",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_Inspector",
        "PARTIAL",
        "Canonical Friend runtime is real and owner-bound; central Command→Friend binding is not yet canonical on main.",
    ),
    CapabilityBinding(
        "agent",
        "AGENT",
        "Agent Runtime",
        "apps/research_os_flutter/lib/src/features/agents/agent_center_page.dart",
        "current/NATIVE_CONTROL_CENTER_OPERATING_CONTRACT.json",
        "owner_special/research_os_friend/agent_runtime.py:AgentRuntime",
        "owner_special/research_os_friend/agent_runtime.py:AgentRuntime.run",
        "owner_special/research_os_friend/agent_runtime.py:AgentTraceEvent",
        "owner_special/research_os_friend/agent_trace_store.py:PersistentAgentTraceStore",
        "owner_special/research_os_friend/agent_runtime.py:AgentRun",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_Inspector",
        "PARTIAL",
        "Agent lifecycle and trace persistence exist; central resolver/executor binding is not yet canonical on main.",
    ),
    CapabilityBinding(
        "github",
        "PLATFORM",
        "GitHub Workbench",
        "apps/research_os_flutter/lib/src/features/github/github_dashboard_page.dart",
        "docs/RESEARCH_OS_SYSTEM_PLATFORM_MATRIX.md",
        "tools/research_os_api/github_status.py",
        "tools/research_os_api/github_status.py",
        "tools/research_os_api/github_status.py",
        "tools/research_os_api/github_status.py",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_Inspector",
        "PARTIAL",
        "GitHub inspection is present; canonical command→workflow execution is a separate binding gap.",
    ),
    CapabilityBinding(
        "factory_v3",
        "FACTORY",
        "V3 Factory",
        "v3/research_os_v3/orchestrator.py",
        "docs/RESEARCH_OS_SYSTEM_PLATFORM_MATRIX.md",
        "v3/research_os_v3/execution.py:FactoryExecutionEngine",
        "v3/research_os_v3/execution.py:FactoryExecutionEngine",
        "v3/research_os_v3/execution.py",
        "v3/research_os_v3/execution.py",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_Inspector",
        "PARTIAL",
        "V3 execution is canonical for V3; Control Center must delegate rather than duplicate it.",
    ),
    CapabilityBinding(
        "assurance",
        "ASSURANCE",
        "Evidence / Assurance",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_EvidenceView",
        "current/NATIVE_CONTROL_CENTER_OPERATING_CONTRACT.json",
        "owner_special/research_os_friend/evidence.py:EvidenceRecorder",
        "owner_special/research_os_friend/evidence.py:EvidenceRecorder",
        "owner_special/research_os_friend/evidence.py:EvidenceRecorder",
        "current/NATIVE_CONTROL_SURFACE_CONTRACT.json",
        "owner_special/flutter_app/lib/src/native_core_workspace_page.dart:_Inspector",
        "PARTIAL",
        "Evidence exists in canonical runtimes, but a universal cross-engine evidence binding is not yet established on main.",
    ),
)


def get_capability(capability_id: str) -> CapabilityBinding:
    for binding in CANONICAL_CAPABILITY_BINDINGS:
        if binding.capability_id == capability_id:
            return binding
    raise KeyError(f"unknown capability_id: {capability_id}")


def iter_capabilities(*, domain: str | None = None) -> Iterable[CapabilityBinding]:
    if domain is None:
        return CANONICAL_CAPABILITY_BINDINGS
    normalized = domain.strip().upper()
    return tuple(item for item in CANONICAL_CAPABILITY_BINDINGS if item.domain.upper() == normalized)


def validate_registry(bindings: Iterable[CapabilityBinding] = CANONICAL_CAPABILITY_BINDINGS) -> tuple[str, ...]:
    items = tuple(bindings)
    errors: list[str] = []
    ids = [item.capability_id for item in items]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append("duplicate capability ids: " + ",".join(duplicates))
    for item in items:
        if item.status not in STATUSES:
            errors.append(f"{item.capability_id}: invalid status")
        if item.executor_ref == "UNKNOWN":
            errors.append(f"{item.capability_id}: executor is unknown")
    return tuple(errors)


__all__ = [
    "CANONICAL_CAPABILITY_BINDINGS",
    "CapabilityBinding",
    "get_capability",
    "iter_capabilities",
    "validate_registry",
]
