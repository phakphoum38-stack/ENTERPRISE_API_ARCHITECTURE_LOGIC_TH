from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .models import CodeArtifact, Evidence, VerificationResult


@dataclass(frozen=True)
class VerificationPolicy:
    require_evidence: bool = True
    minimum_confidence: float = 0.75
    max_artifact_bytes: int = 512_000


class VerificationEngine:
    """Pre-release safety gate for generated artifacts and external evidence."""

    def __init__(self, policy: VerificationPolicy | None = None) -> None:
        self.policy = policy or VerificationPolicy()

    def verify_artifact(self, artifact: CodeArtifact, evidence: tuple[Evidence, ...] = ()) -> VerificationResult:
        checks: list[str] = []
        failures: list[str] = []
        if not artifact.path or PurePosixPath(artifact.path).is_absolute():
            failures.append("artifact path must be relative")
        else:
            checks.append("relative-path")
        if len(artifact.content.encode("utf-8")) > self.policy.max_artifact_bytes:
            failures.append("artifact exceeds configured size limit")
        else:
            checks.append("size-limit")
        if not artifact.content.strip():
            failures.append("artifact is empty")
        else:
            checks.append("non-empty")
        if self.policy.require_evidence:
            trusted = [e for e in evidence if e.confidence >= self.policy.minimum_confidence]
            if not trusted:
                failures.append("no trusted evidence")
            else:
                checks.append("trusted-evidence")
        return VerificationResult(
            passed=not failures,
            checks=tuple(checks),
            failures=tuple(failures),
            evidence=evidence,
        )
