"""Read-only trusted web research policy for Autobot diagnosis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from urllib.parse import urlparse

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_HOST_RE = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
_MAX_TEXT = 2048
_MAX_URL = 4096


class ResearchError(ValueError):
    """Raised when research input violates the safety boundary."""


class SourceKind(str, Enum):
    OFFICIAL_DOCS = "official_docs"
    OFFICIAL_REPOSITORY = "official_repository"
    MAINTAINER = "maintainer"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class MatchState(str, Enum):
    MATCHED = "MATCHED"
    MISMATCHED = "MISMATCHED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ResearchRecord:
    source_url: str
    host: str
    source_kind: SourceKind
    version: str
    environment: str
    source_sha: str
    correlation_id: str
    finding: str
    match_state: MatchState

    def __post_init__(self) -> None:
        _validate_url(self.source_url)
        if not _HOST_RE.fullmatch(self.host):
            raise ResearchError("invalid host")
        if not isinstance(self.source_kind, SourceKind):
            raise ResearchError("invalid source kind")
        for name, value in (("version", self.version), ("environment", self.environment), ("finding", self.finding), ("correlation_id", self.correlation_id)):
            _bounded_text(value, name)
        if not _SHA_RE.fullmatch(self.source_sha):
            raise ResearchError("source_sha must be a 40-character lowercase commit SHA")
        if not isinstance(self.match_state, MatchState):
            raise ResearchError("invalid match state")

    @property
    def fingerprint(self) -> str:
        payload = {
            "source_url": self.source_url,
            "host": self.host,
            "source_kind": self.source_kind.value,
            "version": self.version,
            "environment": self.environment,
            "source_sha": self.source_sha,
            "correlation_id": self.correlation_id,
            "finding": self.finding,
            "match_state": self.match_state.value,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def classify_source(host: str, *, official_hosts: frozenset[str], maintainer_hosts: frozenset[str]) -> SourceKind:
    if host in official_hosts:
        return SourceKind.OFFICIAL_DOCS
    if host in maintainer_hosts:
        return SourceKind.MAINTAINER
    return SourceKind.COMMUNITY


def match_environment(*, observed_version: str, expected_version: str | None, observed_environment: str, expected_environment: str | None) -> MatchState:
    if not observed_version or not observed_environment:
        return MatchState.UNKNOWN
    if expected_version is not None and observed_version != expected_version:
        return MatchState.MISMATCHED
    if expected_environment is not None and observed_environment != expected_environment:
        return MatchState.MISMATCHED
    return MatchState.MATCHED


def validate_research_finding(text: str) -> None:
    _bounded_text(text, "finding")
    lowered = text.lower()
    blocked = ("private key", "ghp_", "sk-proj-", "password", "api_key", "secret", "subprocess", "os.system", "powershell", "cmd.exe", "bash -c", "javascript:", "data:text", "approve", "merge", "release", "install")
    if any(item in lowered for item in blocked):
        raise ResearchError("unsafe research finding")


def _validate_url(value: str) -> None:
    if not isinstance(value, str) or len(value) > _MAX_URL:
        raise ResearchError("URL exceeds bound")
    parsed = urlparse(value)
    if parsed.scheme not in {"https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ResearchError("research URL must be a credential-free HTTPS URL")
    if not _HOST_RE.fullmatch(parsed.hostname):
        raise ResearchError("invalid research host")


def _bounded_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value or len(value) > _MAX_TEXT:
        raise ResearchError(f"{name} must be non-empty and bounded")
