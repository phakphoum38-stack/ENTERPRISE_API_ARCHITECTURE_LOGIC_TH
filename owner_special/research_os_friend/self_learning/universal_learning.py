from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Mapping, Sequence


_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class KnowledgeRecord:
    knowledge_id: str
    kind: str
    domain: str
    statement: str
    source_ids: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class LearningQuestion:
    question_id: str
    statement: str
    status: str


@dataclass(frozen=True)
class LearningDecision:
    decision_id: str
    statement: str
    rationale: str
    status: str


@dataclass(frozen=True)
class LearningAssumption:
    assumption_id: str
    statement: str
    status: str


@dataclass(frozen=True)
class UnderstandingRecord:
    understanding_id: str
    knowledge_id: str
    level: str
    evidence_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class SelfModel:
    model_id: str
    known_ids: tuple[str, ...]
    unknown_ids: tuple[str, ...]
    conflicted_ids: tuple[str, ...]
    active_goal: str
    current_state: str
    next_step: str
    authority_scope: str


class UniversalLearningBoundary:
    """Fail-closed, data-only root for universal knowledge and learning.

    The boundary records knowledge, questions, assumptions, decisions,
    understanding, and self-state. It does not execute work or grant authority.
    """

    KNOWLEDGE_KINDS = frozenset({
        "FACT", "OBSERVATION", "MEASUREMENT", "MODEL", "HYPOTHESIS",
        "THEORY", "INTERPRETATION", "OPINION", "IDEA", "FICTION",
        "SIMULATION", "UNKNOWN",
    })
    DOMAINS = frozenset({
        "LANGUAGE", "MATHEMATICS", "SCIENCE", "ENGINEERING", "TECHNOLOGY",
        "ARTS", "DESIGN", "BUSINESS", "ECONOMICS", "LAW", "HUMANITIES",
        "SOCIAL_SCIENCE", "EDUCATION", "LIFE_AND_WORK", "RESEARCH",
    })
    STATES = frozenset({
        "UNKNOWN", "DISCOVERED", "UNDERSTANDING_PARTIAL", "UNDERSTOOD",
        "PRACTICED", "TESTED", "EVIDENCED", "CONFIDENT", "MASTERED",
        "SUPERSEDED", "CONFLICTED",
    })

    def knowledge(
        self,
        *,
        kind: str,
        domain: str,
        statement: str,
        source_ids: Sequence[str] = (),
        status: str = "UNKNOWN",
    ) -> KnowledgeRecord:
        if kind not in self.KNOWLEDGE_KINDS:
            raise ValueError("unknown knowledge kind")
        if domain not in self.DOMAINS:
            raise ValueError("unknown knowledge domain")
        if not statement.strip():
            raise ValueError("knowledge statement is required")
        if status not in self.STATES:
            raise ValueError("unknown learning state")
        normalized_sources = tuple(sorted(source_ids))
        if any(not item.strip() for item in normalized_sources):
            raise ValueError("source identity cannot be empty")
        payload = {
            "kind": kind,
            "domain": domain,
            "statement": statement,
            "source_ids": normalized_sources,
            "status": status,
        }
        return KnowledgeRecord(
            knowledge_id=self._hash(payload),
            kind=kind,
            domain=domain,
            statement=statement,
            source_ids=normalized_sources,
            status=status,
        )

    def question(self, statement: str, status: str = "UNKNOWN") -> LearningQuestion:
        if not statement.strip():
            raise ValueError("question is required")
        if status not in self.STATES:
            raise ValueError("unknown learning state")
        return LearningQuestion(
            self._hash({"statement": statement, "status": status}),
            statement,
            status,
        )

    def assumption(self, statement: str, status: str = "UNKNOWN") -> LearningAssumption:
        if not statement.strip():
            raise ValueError("assumption is required")
        if status not in self.STATES:
            raise ValueError("unknown learning state")
        return LearningAssumption(
            self._hash({"statement": statement, "status": status}),
            statement,
            status,
        )

    def decision(
        self,
        statement: str,
        rationale: str,
        status: str = "DISCOVERED",
    ) -> LearningDecision:
        if not statement.strip() or not rationale.strip():
            raise ValueError("decision statement and rationale are required")
        if status not in self.STATES:
            raise ValueError("unknown learning state")
        return LearningDecision(
            self._hash({
                "statement": statement,
                "rationale": rationale,
                "status": status,
            }),
            statement,
            rationale,
            status,
        )

    def understanding(
        self,
        *,
        knowledge_id: str,
        level: str,
        evidence_ids: Sequence[str],
        limitations: Sequence[str] = (),
    ) -> UnderstandingRecord:
        self._require_sha256(knowledge_id, "knowledge_id")
        if level not in {"UNKNOWN", "PARTIAL", "UNDERSTOOD", "MASTERED"}:
            raise ValueError("invalid understanding level")
        if level != "UNKNOWN" and not evidence_ids:
            raise ValueError("understanding above UNKNOWN requires evidence")
        normalized_evidence = tuple(sorted(evidence_ids))
        for item in normalized_evidence:
            self._require_sha256(item, "evidence_id")
        normalized_limitations = tuple(sorted(limitations))
        if any(not item.strip() for item in normalized_limitations):
            raise ValueError("understanding limitation cannot be empty")
        return UnderstandingRecord(
            understanding_id=self._hash({
                "knowledge_id": knowledge_id,
                "level": level,
                "evidence_ids": normalized_evidence,
                "limitations": normalized_limitations,
            }),
            knowledge_id=knowledge_id,
            level=level,
            evidence_ids=normalized_evidence,
            limitations=normalized_limitations,
        )

    def self_model(
        self,
        *,
        known_ids: Sequence[str],
        unknown_ids: Sequence[str],
        conflicted_ids: Sequence[str],
        active_goal: str,
        current_state: str,
        next_step: str,
        authority_scope: str,
    ) -> SelfModel:
        if not active_goal.strip() or not current_state.strip() or not next_step.strip():
            raise ValueError("self-model state is incomplete")
        if not authority_scope.strip():
            raise ValueError("authority scope is required")
        known = tuple(sorted(set(known_ids)))
        unknown = tuple(sorted(set(unknown_ids)))
        conflicted = tuple(sorted(set(conflicted_ids)))
        for group in (known, unknown, conflicted):
            for item in group:
                self._require_sha256(item, "self-model identity")
        return SelfModel(
            model_id=self._hash({
                "known_ids": known,
                "unknown_ids": unknown,
                "conflicted_ids": conflicted,
                "active_goal": active_goal,
                "current_state": current_state,
                "next_step": next_step,
                "authority_scope": authority_scope,
            }),
            known_ids=known,
            unknown_ids=unknown,
            conflicted_ids=conflicted,
            active_goal=active_goal,
            current_state=current_state,
            next_step=next_step,
            authority_scope=authority_scope,
        )

    @staticmethod
    def _require_sha256(value: str, field: str) -> None:
        if not _SHA256.fullmatch(value):
            raise ValueError(f"{field} must be a lowercase SHA-256 identity")

    @staticmethod
    def _hash(payload: Mapping) -> str:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(encoded.encode()).hexdigest()
