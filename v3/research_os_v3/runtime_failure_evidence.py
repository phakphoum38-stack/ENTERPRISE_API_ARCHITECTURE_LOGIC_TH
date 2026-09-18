from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimeFailureEvidence:
    target_sha: str
    scenario: str
    observations: Mapping[str, Any]
    evidence_hash: str


class RuntimeFailureEvidenceBuilder:
    """Build deterministic, target-bound evidence without executing runtime work."""

    def __init__(self, target_sha: str) -> None:
        if len(target_sha) != 40 or any(c not in "0123456789abcdef" for c in target_sha):
            raise ValueError("target_sha must be a lowercase 40-character commit SHA")
        self.target_sha = target_sha

    def build(self, scenario: str, observations: Mapping[str, Any]) -> RuntimeFailureEvidence:
        if not scenario or not isinstance(scenario, str):
            raise ValueError("scenario is required")
        payload = {
            "target_sha": self.target_sha,
            "scenario": scenario,
            "observations": observations,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return RuntimeFailureEvidence(self.target_sha, scenario, dict(observations), digest)
