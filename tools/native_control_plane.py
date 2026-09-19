#!/usr/bin/env python3
"""Native Research OS control-plane engines.

A deterministic, bounded orchestration kernel for a future native GUI.
It models four composable engines without creating duplicate schedulers,
queues, memory systems, or authority systems.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandPhase(str, Enum):
    INTENT = "INTENT"
    VALIDATE = "VALIDATE"
    AUTHORIZE = "AUTHORIZE"
    EXECUTE = "EXECUTE"
    OBSERVE = "OBSERVE"
    EVIDENCE = "EVIDENCE"
    COMPLETE = "COMPLETE"


class ViewState(str, Enum):
    DISCOVERED = "DISCOVERED"
    LOADED = "LOADED"
    ACTIVE = "ACTIVE"
    TRANSITIONING = "TRANSITIONING"
    SUSPENDED = "SUSPENDED"
    RECOVERING = "RECOVERING"
    CLOSED = "CLOSED"


class KnowledgeState(str, Enum):
    UNKNOWN = "UNKNOWN"
    DISCOVERED = "DISCOVERED"
    TESTED = "TESTED"
    EVIDENCED = "EVIDENCED"
    CONFIDENT = "CONFIDENT"
    MASTERED = "MASTERED"
    SUPERSEDED = "SUPERSEDED"
    CONFLICTED = "CONFLICTED"


class AssuranceState(str, Enum):
    UNASSESSED = "UNASSESSED"
    OBSERVED = "OBSERVED"
    SUPPORTED = "SUPPORTED"
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Command:
    command_id: str
    intent: str
    action: str
    risk: str = "LOW"
    requires_human: bool = False
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandRecord:
    command: Command
    phases: tuple[CommandPhase, ...]
    outcome: str
    evidence_refs: tuple[str, ...] = ()


@dataclass
class ControlEngine:
    max_commands: int = 100
    history: list[CommandRecord] = field(default_factory=list)

    def validate(self, command: Command) -> None:
        if not command.command_id or not command.intent or not command.action:
            raise ValueError("command identity, intent and action are required")
        if command.requires_human is False and command.risk.upper() in {"HIGH", "CRITICAL"}:
            raise PermissionError("high-risk commands require explicit human control")

    def dispatch(
        self,
        command: Command,
        *,
        authorized: bool = False,
        observed: bool = False,
        evidence_refs: tuple[str, ...] = (),
    ) -> CommandRecord:
        if len(self.history) >= self.max_commands:
            raise RuntimeError("command dispatch bound exceeded")
        self.validate(command)
        phases = [CommandPhase.INTENT, CommandPhase.VALIDATE]
        if command.requires_human or command.risk.upper() in {"HIGH", "CRITICAL"}:
            if not authorized:
                raise PermissionError("human authorization is required")
        phases.append(CommandPhase.AUTHORIZE)
        phases.append(CommandPhase.EXECUTE)
        if observed:
            phases.append(CommandPhase.OBSERVE)
        if evidence_refs:
            phases.append(CommandPhase.EVIDENCE)
        phases.append(CommandPhase.COMPLETE)
        record = CommandRecord(command, tuple(phases), "COMPLETED", evidence_refs)
        self.history.append(record)
        return record


@dataclass(frozen=True)
class View:
    view_id: str
    title: str
    route: str
    state: ViewState = ViewState.DISCOVERED
    reduced_motion: bool = False


@dataclass
class ExperienceEngine:
    views: dict[str, View] = field(default_factory=dict)

    def register(self, view: View) -> View:
        if not view.view_id or not view.route:
            raise ValueError("view identity and route are required")
        if view.view_id in self.views:
            raise ValueError(f"duplicate view: {view.view_id}")
        self.views[view.view_id] = view
        return view

    def transition(self, view_id: str, state: ViewState) -> View:
        current = self.views[view_id]
        updated = View(current.view_id, current.title, current.route, state, current.reduced_motion)
        self.views[view_id] = updated
        return updated


@dataclass(frozen=True)
class KnowledgeObject:
    object_id: str
    kind: str
    state: KnowledgeState = KnowledgeState.UNKNOWN
    context: dict[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()


@dataclass
class KnowledgeEngine:
    objects: dict[str, KnowledgeObject] = field(default_factory=dict)

    def register(self, obj: KnowledgeObject) -> KnowledgeObject:
        if not obj.object_id or not obj.kind:
            raise ValueError("knowledge identity and kind are required")
        if obj.object_id in self.objects:
            raise ValueError(f"duplicate knowledge object: {obj.object_id}")
        self.objects[obj.object_id] = obj
        return obj

    def transition(self, object_id: str, state: KnowledgeState, *, evidence_refs: tuple[str, ...] = ()) -> KnowledgeObject:
        current = self.objects[object_id]
        refs = evidence_refs or current.evidence_refs
        if state in {KnowledgeState.CONFIDENT, KnowledgeState.MASTERED} and not refs:
            raise ValueError("confidence/mastery requires evidence references")
        updated = KnowledgeObject(current.object_id, current.kind, state, current.context, refs)
        self.objects[object_id] = updated
        return updated


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    subject_id: str
    source_ref: str
    fingerprint: str
    state: AssuranceState = AssuranceState.UNASSESSED


@dataclass
class AssuranceEngine:
    evidence: dict[str, Evidence] = field(default_factory=dict)

    def record(self, item: Evidence) -> Evidence:
        if not item.evidence_id or not item.subject_id or not item.source_ref:
            raise ValueError("evidence identity, subject and source are required")
        if len(item.fingerprint) != 64:
            raise ValueError("evidence fingerprint must be SHA-256")
        if item.evidence_id in self.evidence:
            raise ValueError(f"duplicate evidence: {item.evidence_id}")
        self.evidence[item.evidence_id] = item
        return item

    def verify(self, evidence_id: str) -> Evidence:
        current = self.evidence[evidence_id]
        updated = Evidence(current.evidence_id, current.subject_id, current.source_ref, current.fingerprint, AssuranceState.VERIFIED)
        self.evidence[evidence_id] = updated
        return updated


@dataclass
class ResearchOSControlPlane:
    """Single composition root for the four engines."""

    control: ControlEngine = field(default_factory=ControlEngine)
    experience: ExperienceEngine = field(default_factory=ExperienceEngine)
    knowledge: KnowledgeEngine = field(default_factory=KnowledgeEngine)
    assurance: AssuranceEngine = field(default_factory=AssuranceEngine)

    def inspect(self, object_id: str) -> dict[str, Any]:
        """Return a bounded universal inspector record."""
        obj = self.knowledge.objects.get(object_id)
        evidence = [e for e in self.assurance.evidence.values() if e.subject_id == object_id]
        if obj is None and not evidence:
            raise KeyError(object_id)
        return {
            "object_id": object_id,
            "knowledge": None if obj is None else {
                "kind": obj.kind,
                "state": obj.state.value,
                "evidence_refs": list(obj.evidence_refs),
            },
            "evidence": [
                {"id": e.evidence_id, "source_ref": e.source_ref, "state": e.state.value}
                for e in evidence
            ],
        }

    def summary(self) -> dict[str, int]:
        return {
            "commands": len(self.control.history),
            "views": len(self.experience.views),
            "knowledge_objects": len(self.knowledge.objects),
            "evidence": len(self.assurance.evidence),
        }
