"""Canonical operation-level delegation bindings for existing Research OS executors.

This module is declarative: it never executes a capability. It closes the
semantic gap between a prepared Control Center command and the exact operation
that an existing executor is allowed to own.

The router uses this registry to prevent a caller from relabeling a mutating
operation as READ_ONLY, and to prevent evidence/assurance surfaces from being
treated as execution engines.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DelegationOperation:
    action: str
    action_class: str
    executor_method: str


@dataclass(frozen=True)
class DelegationBinding:
    capability_id: str
    executor_ref: str
    operations: tuple[DelegationOperation, ...]
    execution_supported: bool = True


CANONICAL_DELEGATIONS: tuple[DelegationBinding, ...] = (
    DelegationBinding(
        "friend",
        "owner_special/research_os_friend/friend_runtime_contract.py:FriendRuntimeContract",
        (
            DelegationOperation("inspect status", "READ_ONLY", "snapshot"),
            DelegationOperation("inspect tool health", "READ_ONLY", "tool_health"),
            DelegationOperation("ask friend", "MUTATION", "ask"),
            DelegationOperation("run agent", "MUTATION", "run_agent"),
        ),
    ),
    DelegationBinding(
        "agent",
        "owner_special/research_os_friend/agent_runtime.py:AgentRuntime",
        (
            DelegationOperation("inspect run", "READ_ONLY", "get"),
            DelegationOperation("list runs", "READ_ONLY", "list_runs"),
            DelegationOperation("run agent", "MUTATION", "run"),
        ),
    ),
    DelegationBinding(
        "github",
        "tools/research_os_api/github_status.py",
        (
            DelegationOperation("inspect repository", "READ_ONLY", "dashboard"),
            DelegationOperation("inspect artifacts", "READ_ONLY", "artifacts"),
        ),
    ),
    DelegationBinding(
        "factory_v3",
        "v3/research_os_v3/execution.py:FactoryExecutionEngine",
        (
            DelegationOperation("execute factory plan", "MUTATION", "execute"),
        ),
    ),
    DelegationBinding(
        "assurance",
        "owner_special/research_os_friend/evidence.py:EvidenceRecorder",
        (),
        execution_supported=False,
    ),
)


def get_delegation(capability_id: str) -> DelegationBinding:
    for binding in CANONICAL_DELEGATIONS:
        if binding.capability_id == capability_id:
            return binding
    raise KeyError(f"unknown capability_id: {capability_id}")


def get_operation(capability_id: str, action: str) -> DelegationOperation:
    binding = get_delegation(capability_id)
    for operation in binding.operations:
        if operation.action == action:
            return operation
    raise KeyError(f"unsupported action for {capability_id}: {action}")


def validate_delegations() -> tuple[str, ...]:
    errors: list[str] = []
    capability_ids = {item.capability_id for item in CANONICAL_DELEGATIONS}
    expected = {"friend", "agent", "github", "factory_v3", "assurance"}
    missing = expected - capability_ids
    if missing:
        errors.append("missing capability bindings: " + ",".join(sorted(missing)))
    for binding in CANONICAL_DELEGATIONS:
        seen: set[str] = set()
        for operation in binding.operations:
            if operation.action in seen:
                errors.append(f"{binding.capability_id}: duplicate action {operation.action}")
            seen.add(operation.action)
            if operation.action_class not in {"READ_ONLY", "MUTATION"}:
                errors.append(
                    f"{binding.capability_id}: invalid action class {operation.action_class}"
                )
            if not operation.executor_method:
                errors.append(f"{binding.capability_id}: missing executor method")
        if not binding.execution_supported and binding.operations:
            errors.append(f"{binding.capability_id}: non-executable binding has operations")
    return tuple(errors)


__all__ = [
    "CANONICAL_DELEGATIONS",
    "DelegationBinding",
    "DelegationOperation",
    "get_delegation",
    "get_operation",
    "validate_delegations",
]
