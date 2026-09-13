"""Bounded governance primitives for the Research OS Generator/Autobot boundary.

The module is intentionally side-effect free. It models policy and state; it does
not dispatch workflows, mutate refs, approve releases, or publish artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_TEXT = 2048
_MAX_FILES = 128
_MAX_ACTIONS = 512


class GovernanceError(ValueError):
    """Raised when a governed state or transition is unsafe."""


class FailureClass(str, Enum):
    CODE = "CODE"
    TEST = "TEST"
    DEPENDENCY = "DEPENDENCY"
    ENVIRONMENT = "ENVIRONMENT"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    IDENTITY = "IDENTITY"
    EVIDENCE = "EVIDENCE"
    POLICY = "POLICY"
    PROVENANCE = "PROVENANCE"
    UNKNOWN = "UNKNOWN"


RETRYABLE_FAILURES = frozenset({
    FailureClass.DEPENDENCY,
    FailureClass.ENVIRONMENT,
    FailureClass.INFRASTRUCTURE,
})


class Capability(str, Enum):
    READ_REPOSITORY = "read_repository"
    READ_CI = "read_ci"
    RESEARCH_WEB = "research_web"
    MODIFY_PERMITTED_FILES = "modify_permitted_files"
    CREATE_COMMIT = "create_commit"


FORBIDDEN_CAPABILITIES = frozenset({
    "approve",
    "merge",
    "release",
    "install_as_release_authority",
    "bypass_gate",
    "rewrite_evidence",
    "escalate_capability",
})


@dataclass(frozen=True)
class GenerationManifest:
    """Bounded description of a generator output set."""

    generator_id: str
    generator_version: str
    input_sha: str
    outputs: tuple[tuple[str, str], ...]
    schema: str

    def __post_init__(self) -> None:
        _validate_sha(self.input_sha, "input_sha")
        _bounded_text(self.generator_id, "generator_id")
        _bounded_text(self.generator_version, "generator_version")
        _bounded_text(self.schema, "schema")
        if not self.outputs or len(self.outputs) > _MAX_FILES:
            raise GovernanceError("outputs must contain a bounded non-empty set")
        seen: set[str] = set()
        for path, digest in self.outputs:
            _bounded_text(path, "output path")
            if path in seen:
                raise GovernanceError("duplicate generated output path")
            seen.add(path)
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise GovernanceError("output digest must be a SHA-256 hex digest")


@dataclass(frozen=True)
class AutobotAction:
    """One immutable ledger entry describing an attempted autonomous action."""

    job_id: str
    correlation_id: str
    source_sha: str
    attempt: int
    action: str
    reason: str
    result: str
    commit_sha: str | None = None
    ci_run_id: str | None = None

    def __post_init__(self) -> None:
        _validate_sha(self.source_sha, "source_sha")
        for name, value in (
            ("job_id", self.job_id),
            ("correlation_id", self.correlation_id),
            ("action", self.action),
            ("reason", self.reason),
            ("result", self.result),
        ):
            _bounded_text(value, name)
        if self.attempt < 0:
            raise GovernanceError("attempt cannot be negative")
        if self.commit_sha is not None:
            _validate_sha(self.commit_sha, "commit_sha")
        if self.ci_run_id is not None:
            _bounded_text(self.ci_run_id, "ci_run_id")


class ActionLedger:
    """Append-only in-memory ledger with deterministic event fingerprints."""

    def __init__(self) -> None:
        self._entries: list[AutobotAction] = []

    def append(self, entry: AutobotAction) -> str:
        if len(self._entries) >= _MAX_ACTIONS:
            raise GovernanceError("action ledger bound exhausted")
        self._entries.append(entry)
        material = "\n".join(
            f"{item.job_id}|{item.correlation_id}|{item.source_sha}|{item.attempt}|"
            f"{item.action}|{item.reason}|{item.result}|{item.commit_sha or ''}|{item.ci_run_id or ''}"
            for item in self._entries
        ).encode("utf-8")
        return hashlib.sha256(material).hexdigest()

    @property
    def entries(self) -> tuple[AutobotAction, ...]:
        return tuple(self._entries)


@dataclass(frozen=True)
class RepairBudget:
    max_attempts: int = 3
    max_files_per_repair: int = 16

    def __post_init__(self) -> None:
        if not 1 <= self.max_attempts <= 10:
            raise GovernanceError("max_attempts must be between 1 and 10")
        if not 1 <= self.max_files_per_repair <= _MAX_FILES:
            raise GovernanceError("max_files_per_repair is outside the safe bound")

    def allows(self, attempt: int, changed_files: int) -> bool:
        return 0 <= attempt < self.max_attempts and 0 <= changed_files <= self.max_files_per_repair


@dataclass(frozen=True)
class CircuitBreaker:
    max_same_failure: int = 2
    max_total_attempts: int = 5

    def __post_init__(self) -> None:
        if not 1 <= self.max_same_failure <= 10:
            raise GovernanceError("max_same_failure is outside the safe bound")
        if not 1 <= self.max_total_attempts <= 20:
            raise GovernanceError("max_total_attempts is outside the safe bound")

    def should_stop(self, fingerprints: tuple[str, ...]) -> bool:
        if len(fingerprints) >= self.max_total_attempts:
            return True
        if not fingerprints:
            return False
        return fingerprints.count(fingerprints[-1]) >= self.max_same_failure


def classify_failure(value: str, *, integrity_signal: bool = False) -> FailureClass:
    """Classify conservatively; ambiguous failures become UNKNOWN."""
    if not isinstance(value, str) or not value.strip():
        return FailureClass.UNKNOWN
    text = value.lower()
    if integrity_signal:
        return FailureClass.EVIDENCE
    rules = (
        (FailureClass.IDENTITY, ("sha mismatch", "commit mismatch", "wrong sha")),
        (FailureClass.PROVENANCE, ("provenance", "artifact lineage", "source lineage")),
        (FailureClass.POLICY, ("approval", "bypass", "authority", "permission denied")),
        (FailureClass.DEPENDENCY, ("dependency", "package version", "pub get", "pip install")),
        (FailureClass.INFRASTRUCTURE, ("runner unavailable", "service unavailable", "actions runner")),
        (FailureClass.ENVIRONMENT, ("environment", "sdk not found", "toolchain")),
        (FailureClass.TEST, ("test failed", "assertionerror", "flutter test")),
        (FailureClass.CODE, ("syntaxerror", "typeerror", "compile error", "build failed")),
    )
    matches = [kind for kind, needles in rules if any(needle in text for needle in needles)]
    return matches[0] if len(matches) == 1 else FailureClass.UNKNOWN


def retry_allowed(failure_class: FailureClass, attempt: int, budget: RepairBudget) -> bool:
    if not isinstance(failure_class, FailureClass):
        return False
    return failure_class in RETRYABLE_FAILURES and budget.allows(attempt, 0)


def validate_capabilities(capabilities: Mapping[str, Any]) -> frozenset[str]:
    """Validate an explicit capability set and reject authority escalation."""
    if not isinstance(capabilities, Mapping):
        raise GovernanceError("capabilities must be a mapping")
    raw = capabilities.get("allowed", ())
    if not isinstance(raw, (list, tuple, set, frozenset)):
        raise GovernanceError("allowed capabilities must be a collection")
    values = frozenset(str(item) for item in raw)
    forbidden = values & FORBIDDEN_CAPABILITIES
    if forbidden:
        raise GovernanceError(f"forbidden capability requested: {sorted(forbidden)}")
    if not values.issubset({cap.value for cap in Capability}):
        raise GovernanceError("unknown capability requested")
    return values


def validate_repair_scope(paths: tuple[str, ...], budget: RepairBudget) -> tuple[str, ...]:
    """Reject empty, duplicate, or protected paths and enforce a small repair scope."""
    if not paths:
        raise GovernanceError("repair must change at least one file")
    if len(paths) > budget.max_files_per_repair:
        raise GovernanceError("repair exceeds file budget")
    if len(set(paths)) != len(paths):
        raise GovernanceError("repair contains duplicate paths")
    protected = (
        ".github/workflows/",
        "owner_special/installer/",
        "owner_special/scripts/verify-installed-owner-provenance.ps1",
        "owner_special/research_os_friend/identity_foundation.py",
    )
    for path in paths:
        _bounded_text(path, "repair path")
        if any(path.startswith(prefix) for prefix in protected):
            raise GovernanceError("protected repair path")
    return paths


def _validate_sha(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise GovernanceError(f"{name} must be a 40-character lowercase commit SHA")


def _bounded_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value or len(value) > _MAX_TEXT:
        raise GovernanceError(f"{name} must be non-empty and bounded")
