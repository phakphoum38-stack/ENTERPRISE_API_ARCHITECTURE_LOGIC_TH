from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    content: str
    timestamp: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    source: str
    title: str
    url: str | None = None
    confidence: float = 0.0
    retrieved_at: datetime = field(default_factory=utc_now)
    notes: str = ""


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    capabilities: tuple[str, ...]
    entrypoint: str
    enabled: bool = True
    permissions: tuple[str, ...] = ()


@dataclass(frozen=True)
class CodeArtifact:
    path: str
    content: str
    language: str
    purpose: str


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
