#!/usr/bin/env python3
"""Bounded universal control surface for the native Research OS Control Center.

This module is a pure model. Network, filesystem, process, GitHub and other
external I/O remain in existing adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Iterable, Mapping


SEARCH_DOMAINS = {
    "TASK", "KNOWLEDGE", "SOURCE", "EVIDENCE", "SERVICE", "TOOL",
    "PROJECT", "SNAPSHOT", "FAILURE", "DECISION", "DESIGN", "COMPONENT",
}
LIFECYCLE = (
    "INTENT", "VALIDATE", "PREPARE", "AUTHORIZE", "EXECUTE",
    "OBSERVE", "EVIDENCE", "COMPLETE", "RECOVER",
)
HUMAN_ACTIONS = {"APPROVE", "AUTHORIZE", "RELEASE", "HIGH_RISK_ACTION"}


@dataclass(frozen=True)
class SurfaceObject:
    object_id: str
    object_type: str
    title: str
    state: str = "UNKNOWN"
    owner: str = "UNKNOWN"
    version: str = "UNKNOWN"
    relations: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    provenance: str | None = None
    evidence: tuple[str, ...] = ()
    confidence: str = "UNKNOWN"
    risk: str = "UNKNOWN"
    history: tuple[str, ...] = ()
    recovery: str = "UNKNOWN"
    successor: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if not self.object_id.strip() or not self.object_type.strip():
            raise ValueError("object identity and type are required")
        if not self.title.strip():
            raise ValueError("object title is required")


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    label: str
    intent: str
    target: str = ""
    mode: str = "SIMULATION"
    risk: str = "LOW"
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.command_id.strip() or not self.label.strip() or not self.intent.strip():
            raise ValueError("command identity, label and intent are required")
        if self.mode not in {"LIVE", "SIMULATION", "DRY_RUN", "REPLAY"}:
            raise ValueError(f"unsupported mode: {self.mode}")


@dataclass(frozen=True)
class SearchHit:
    object_id: str
    object_type: str
    title: str
    score: int
    state: str


@dataclass(frozen=True)
class TraceStep:
    object_id: str
    relation: str
    depth: int


class UniversalControlSurface:
    """One bounded read/search/prepare surface; it never grants authority."""

    def __init__(
        self,
        *,
        max_search_results: int = 100,
        max_relations: int = 256,
        max_evidence: int = 256,
        max_trace_depth: int = 32,
    ) -> None:
        for name, value in (
            ("max_search_results", max_search_results),
            ("max_relations", max_relations),
            ("max_evidence", max_evidence),
            ("max_trace_depth", max_trace_depth),
        ):
            if value < 1:
                raise ValueError(f"{name} must be positive")
        self.max_search_results = max_search_results
        self.max_relations = max_relations
        self.max_evidence = max_evidence
        self.max_trace_depth = max_trace_depth
        self._objects: dict[str, SurfaceObject] = {}
        self._commands: dict[str, CommandSpec] = {}

    def register_object(self, obj: SurfaceObject) -> None:
        if obj.object_id in self._objects:
            raise ValueError(f"duplicate object_id: {obj.object_id}")
        if obj.object_type.upper() not in SEARCH_DOMAINS and obj.object_type.upper() != "UNKNOWN":
            raise ValueError(f"unsupported search domain: {obj.object_type}")
        self._objects[obj.object_id] = obj

    def register_command(self, command: CommandSpec) -> None:
        if command.command_id in self._commands:
            raise ValueError(f"duplicate command_id: {command.command_id}")
        self._commands[command.command_id] = command

    def search(self, query: str, *, domain: str | None = None, limit: int | None = None) -> tuple[SearchHit, ...]:
        term = query.strip().lower()
        if not term:
            raise ValueError("search query is required")
        if domain is not None and domain.upper() not in SEARCH_DOMAINS:
            raise ValueError(f"unsupported search domain: {domain}")
        cap = min(limit or self.max_search_results, self.max_search_results)
        if cap < 1:
            raise ValueError("limit must be positive")
        hits: list[SearchHit] = []
        for obj in self._objects.values():
            if domain is not None and obj.object_type.upper() != domain.upper():
                continue
            haystack = " ".join(
                (obj.object_id, obj.object_type, obj.title, obj.state, *obj.relations, *obj.dependencies)
            ).lower()
            score = sum(1 for token in term.split() if token in haystack)
            if score:
                hits.append(SearchHit(obj.object_id, obj.object_type, obj.title, score, obj.state))
        hits.sort(key=lambda hit: (-hit.score, hit.object_id))
        return tuple(hits[:cap])

    def inspect(self, object_id: str) -> SurfaceObject:
        try:
            return self._objects[object_id]
        except KeyError as exc:
            raise KeyError(f"unknown object_id: {object_id}") from exc

    def trace(self, object_id: str, *, relation: str = "RELATION", depth: int = 1) -> tuple[TraceStep, ...]:
        if depth < 1 or depth > self.max_trace_depth:
            raise ValueError("trace depth outside bounded range")
        root = self.inspect(object_id)
        steps: list[TraceStep] = [TraceStep(root.object_id, relation, 0)]
        frontier = list(root.relations[: self.max_relations])
        seen = {root.object_id}
        for current_depth in range(1, depth + 1):
            next_frontier: list[str] = []
            for ref in frontier:
                if ref in seen:
                    continue
                seen.add(ref)
                steps.append(TraceStep(ref, relation, current_depth))
                child = self._objects.get(ref)
                if child is not None:
                    next_frontier.extend(child.relations[: self.max_relations])
            frontier = next_frontier
            if not frontier:
                break
        return tuple(steps)

    def why(self, object_id: str) -> tuple[TraceStep, ...]:
        """Return a bounded causal/lineage-oriented trace without claiming truth."""
        return self.trace(object_id, relation="WHY", depth=self.max_trace_depth)

    def prepare_command(self, command_id: str) -> str:
        command = self._commands.get(command_id)
        if command is None:
            raise KeyError(f"unknown command_id: {command_id}")
        payload = {
            "command_id": command.command_id,
            "label": command.label,
            "intent": command.intent,
            "target": command.target,
            "mode": command.mode,
            "risk": command.risk,
            "keywords": list(command.keywords),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def human_required(action: str) -> bool:
        return action.upper() in HUMAN_ACTIONS

    def system_map(self) -> Mapping[str, tuple[str, ...]]:
        return {
            "CORE": tuple(sorted(obj.object_id for obj in self._objects.values() if obj.object_type.upper() in {"TASK", "KNOWLEDGE"})),
            "ASSURANCE": tuple(sorted(obj.object_id for obj in self._objects.values() if obj.object_type.upper() in {"EVIDENCE", "SOURCE"})),
            "PLATFORM": tuple(sorted(obj.object_id for obj in self._objects.values() if obj.object_type.upper() in {"SERVICE", "TOOL"})),
            "EXPERIENCE": tuple(sorted(obj.object_id for obj in self._objects.values() if obj.object_type.upper() in {"DESIGN", "COMPONENT"})),
        }

    def fingerprint(self) -> str:
        payload = {
            "objects": [obj.__dict__ for obj in sorted(self._objects.values(), key=lambda item: item.object_id)],
            "commands": [cmd.__dict__ for cmd in sorted(self._commands.values(), key=lambda item: item.command_id)],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=list).encode()
        return hashlib.sha256(raw).hexdigest()


__all__ = [
    "CommandSpec",
    "SearchHit",
    "SurfaceObject",
    "TraceStep",
    "UniversalControlSurface",
]
