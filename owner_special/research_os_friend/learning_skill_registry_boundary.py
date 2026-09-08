from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from .self_learning.models import LearnedSkillCandidate
from .self_learning.registry import LearnedSkillRegistry

_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|authorization|bearer|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess|shell|process|mcp|computer[_-]?use|release|merge|install|dispatch|bypass|approval|execute|executor)",
    re.I,
)


class LearnedSkillRegistryBoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class LearnedSkillRegistryRequest:
    owner: str
    record_fingerprint: str
    receipt_fingerprint: str


class LearnedSkillRegistryBoundary:
    """Materialize an explicit H10 promotion receipt into the learned-skill registry."""

    def commit(
        self,
        request: LearnedSkillRegistryRequest,
        receipt: dict[str, Any],
        registry: LearnedSkillRegistry,
    ) -> LearnedSkillCandidate:
        self._validate_request(request)
        self._validate_receipt(receipt)
        if request.owner != receipt.get("owner"):
            raise LearnedSkillRegistryBoundaryError("owner mismatch")
        if request.record_fingerprint != receipt.get("record_fingerprint"):
            raise LearnedSkillRegistryBoundaryError("promotion record mismatch")
        if request.receipt_fingerprint != receipt.get("receipt_fingerprint"):
            raise LearnedSkillRegistryBoundaryError("promotion receipt mismatch")

        candidate_data = receipt["candidate"]
        self._scan(candidate_data, 0)
        candidate = LearnedSkillCandidate(
            name=candidate_data["name"],
            goal=candidate_data["goal"],
            procedure=tuple(candidate_data["procedure"]),
            evidence=tuple(candidate_data.get("evidence", ())),
            confidence=float(candidate_data.get("confidence", 0.0)),
            status="candidate",
            version=int(candidate_data.get("version", 1)),
            metadata=dict(candidate_data.get("metadata", {})),
        )
        return registry.promote(candidate)

    def _validate_request(self, request: LearnedSkillRegistryRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearnedSkillRegistryBoundaryError("invalid owner")
        if not _FP_RE.fullmatch(request.record_fingerprint) or not _FP_RE.fullmatch(request.receipt_fingerprint):
            raise LearnedSkillRegistryBoundaryError("invalid fingerprint")

    def _validate_receipt(self, receipt: Any) -> None:
        if not isinstance(receipt, dict) or receipt.get("schema") != "research-os-learning-promotion-receipt/v1":
            raise LearnedSkillRegistryBoundaryError("invalid H10 promotion receipt")
        if receipt.get("promotion_authority") != "H10":
            raise LearnedSkillRegistryBoundaryError("promotion authority must be H10")
        if receipt.get("approved") is not True:
            raise LearnedSkillRegistryBoundaryError("promotion receipt is not approved")
        if receipt.get("read_only") is not True or receipt.get("authority") != "none":
            raise LearnedSkillRegistryBoundaryError("receipt authority contract violated")
        if not _FP_RE.fullmatch(str(receipt.get("record_fingerprint", ""))):
            raise LearnedSkillRegistryBoundaryError("invalid record fingerprint")
        candidate = receipt.get("candidate")
        if not isinstance(candidate, dict):
            raise LearnedSkillRegistryBoundaryError("missing candidate")
        for key in ("name", "goal", "procedure"):
            if key not in candidate:
                raise LearnedSkillRegistryBoundaryError(f"missing candidate field: {key}")
        if not isinstance(candidate["name"], str) or not candidate["name"] or _BLOCKED.search(candidate["name"]):
            raise LearnedSkillRegistryBoundaryError("invalid candidate name")
        if not isinstance(candidate["goal"], str) or _BLOCKED.search(candidate["goal"]):
            raise LearnedSkillRegistryBoundaryError("invalid candidate goal")
        if not isinstance(candidate["procedure"], (list, tuple)) or not candidate["procedure"]:
            raise LearnedSkillRegistryBoundaryError("invalid candidate procedure")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > 8:
            raise LearnedSkillRegistryBoundaryError("candidate depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > 64:
                raise LearnedSkillRegistryBoundaryError("candidate object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearnedSkillRegistryBoundaryError("unsafe candidate key")
                self._scan(item, depth + 1)
        elif isinstance(value, (list, tuple)):
            if len(value) > 64:
                raise LearnedSkillRegistryBoundaryError("candidate list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearnedSkillRegistryBoundaryError("unsafe candidate value")
