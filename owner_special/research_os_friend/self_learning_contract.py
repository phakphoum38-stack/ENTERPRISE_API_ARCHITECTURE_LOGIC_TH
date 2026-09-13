"""Fail-closed governance boundary for Friend self-learning in H5."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping
from typing import Any

from .self_learning import SelfLearningEngine


class SelfLearningContractError(ValueError):
    """Raised when a learning proposal is unsafe, stale, or unbound."""


class SelfLearningContract:
    """Bind bounded learning proposals to Owner/source identity and evidence."""

    SCHEMA = "research-os-self-learning/v1"
    MAX_TEXT = 2048
    MAX_BYTES = 64 * 1024
    MAX_EVIDENCE = 64
    MAX_DEPTH = 6
    SHA_RE = re.compile(r"^[0-9a-f]{40}$")
    CORRELATION_RE = re.compile(r"^[A-Za-z0-9._:-]{1,2048}$")
    _ALLOWED_STRUCTURAL_KEYS = frozenset({"approved_skills", "approval_required"})
    BLOCKED_KEYS = re.compile(
        r"(?:approval|approve|authorize|permission|release|merge|dispatch|"
        r"credential|secret|token|password|private.?key|callback|callable|"
        r"function|lambda|eval|exec|shell|command|process|subprocess|"
        r"computer.?use|mcp)",
        re.I,
    )
    BLOCKED_VALUES = re.compile(
        r"(?:BEGIN PRIVATE KEY|ghp_|sk-proj-|api.?key\s*=|javascript:|data:text/html|"
        r"powershell|cmd\.exe|bash\s+-c|os\.system|child_process)",
        re.I,
    )

    def __init__(self, engine: SelfLearningEngine, *, owner_id: str, source_sha: str) -> None:
        self._validate_text(owner_id, "owner_id")
        self._validate_sha(source_sha)
        if not isinstance(engine, SelfLearningEngine):
            raise SelfLearningContractError("engine must be SelfLearningEngine")
        self._engine = engine
        self.owner_id = owner_id
        self.source_sha = source_sha

    def propose_and_promote(
        self,
        *,
        name: str,
        goal: str,
        procedure: tuple[str, ...],
        evidence: tuple[str, ...],
        confidence: float,
        run_correlation_id: str,
    ) -> dict[str, Any] | None:
        self._validate_text(name, "name")
        self._validate_text(goal, "goal")
        self._validate_correlation(run_correlation_id)
        if not isinstance(procedure, tuple) or not procedure:
            raise SelfLearningContractError("procedure must be a non-empty tuple")
        if not isinstance(evidence, tuple) or not evidence:
            raise SelfLearningContractError("learning requires evidence")
        if len(evidence) > self.MAX_EVIDENCE:
            raise SelfLearningContractError("evidence exceeds bound")
        if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
            raise SelfLearningContractError("confidence must be between 0 and 1")
        self._walk_safe({"name": name, "goal": goal, "procedure": procedure, "evidence": evidence})

        candidate = self._engine.propose(
            name=name,
            goal=goal,
            procedure=procedure,
            evidence=evidence,
            confidence=float(confidence),
        )
        approved = self._engine.learn(candidate)
        if approved is None:
            return None
        result = {
            "schema": self.SCHEMA,
            "owner_id": self.owner_id,
            "source_sha": self.source_sha,
            "run_correlation_id": run_correlation_id,
            "skill_id": approved.name,
            "goal": approved.goal,
            "procedure": tuple(approved.procedure),
            "evidence": tuple(approved.evidence),
            "confidence": approved.confidence,
            "core_mutation": False,
            "promoted": True,
        }
        self._validate_payload(result)
        return copy.deepcopy(result)

    def snapshot(self) -> dict[str, Any]:
        snapshot = copy.deepcopy(self._engine.snapshot())
        result = {
            "schema": self.SCHEMA,
            "owner_id": self.owner_id,
            "source_sha": self.source_sha,
            "read_only": True,
            "learning": snapshot,
        }
        self._validate_payload(result)
        return copy.deepcopy(result)

    def _validate_payload(self, value: Mapping[str, Any]) -> None:
        self._walk_safe(value)
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise SelfLearningContractError("learning payload exceeds byte bound")

    def _walk_safe(self, value: Any, *, depth: int = 0) -> None:
        if depth > self.MAX_DEPTH:
            raise SelfLearningContractError("learning payload nesting exceeds bound")
        if isinstance(value, Mapping):
            if len(value) > self.MAX_EVIDENCE:
                raise SelfLearningContractError("learning mapping exceeds bound")
            for key, child in value.items():
                if (
                    not isinstance(key, str)
                    or len(key) > self.MAX_TEXT
                    or (
                        self.BLOCKED_KEYS.search(key)
                        and key not in self._ALLOWED_STRUCTURAL_KEYS
                    )
                ):
                    raise SelfLearningContractError("learning payload contains forbidden field")
                self._walk_safe(child, depth=depth + 1)
            return
        if isinstance(value, (list, tuple)):
            if len(value) > self.MAX_EVIDENCE:
                raise SelfLearningContractError("learning collection exceeds bound")
            for child in value:
                self._walk_safe(child, depth=depth + 1)
            return
        if isinstance(value, str):
            if len(value) > self.MAX_TEXT or self.BLOCKED_VALUES.search(value):
                raise SelfLearningContractError("learning payload contains forbidden value")
            return
        if value is None or isinstance(value, (bool, int, float)):
            return
        raise SelfLearningContractError("learning payload contains dynamic value")

    def _validate_text(self, value: str, name: str) -> None:
        if not isinstance(value, str) or not value or len(value) > self.MAX_TEXT:
            raise SelfLearningContractError(f"{name} is invalid or oversized")

    def _validate_sha(self, value: str) -> None:
        if not isinstance(value, str) or not self.SHA_RE.fullmatch(value):
            raise SelfLearningContractError("source SHA must be exact lowercase hexadecimal")

    def _validate_correlation(self, value: str) -> None:
        if not isinstance(value, str) or not self.CORRELATION_RE.fullmatch(value):
            raise SelfLearningContractError("run correlation ID is invalid or oversized")
