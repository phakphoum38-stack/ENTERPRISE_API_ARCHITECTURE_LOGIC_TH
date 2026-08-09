#!/usr/bin/env python3
"""Research OS AI Brain Core foundation.

This module owns the model-independent control plane for understanding a goal,
tracking working state, resolving capabilities, producing an auditable plan,
and verifying evidence. It intentionally does not expose hidden model
chain-of-thought and does not execute tools directly yet.

Brain Core is provider-neutral. Context assembly, skills and deterministic
risk/decision policy are composed by ``v2_brain_runtime``. Tool execution,
knowledge adapters and model execution remain permissioned ports that can be
attached in later slices without replacing this core.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from agent_platform import AgentRegistry, REGISTRY


SENSITIVE_KEY_RE = re.compile(
    r"(?:api[_-]?key|authorization|bearer|cookie|credential|password|secret|token)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BrainIdentity:
    system: str = "Research OS"
    component: str = "AI Brain Core"
    version: str = "0.2.0"
    role: str = "model-independent intelligence control plane"


@dataclass(frozen=True)
class BrainConstitution:
    principles: tuple[str, ...] = (
        "Long-term First",
        "One Truth",
        "AI is a Team Member",
        "Every Change Has Evidence",
        "Documentation Never Lags Behind Code",
        "Quality Is Continuous",
    )
    invariants: tuple[str, ...] = (
        "Do not claim completion without verification evidence.",
        "Do not treat missing information as fact.",
        "Do not expose secrets through plans, memory, events, or diagnostics.",
        "Respect permission and approval boundaries before state-changing actions.",
        "Keep provider selection separate from durable Research OS intelligence.",
    )


@dataclass(frozen=True)
class BrainGoal:
    goal_id: str
    objective: str
    intent: tuple[str, ...]
    constraints: tuple[str, ...]
    known: tuple[str, ...]
    unknown: tuple[str, ...]
    definition_of_done: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityMatch:
    capability: str
    agents: tuple[str, ...]
    available: bool


@dataclass(frozen=True)
class BrainPlanStep:
    step_id: str
    action: str
    capability: str
    reason: str
    depends_on: tuple[str, ...] = ()
    requires_approval: bool = False
    status: str = "planned"


@dataclass(frozen=True)
class BrainPlan:
    plan_id: str
    session_id: str
    goal: BrainGoal
    required_capabilities: tuple[str, ...]
    capability_matches: tuple[CapabilityMatch, ...]
    steps: tuple[BrainPlanStep, ...]
    executable: bool
    blocked_reasons: tuple[str, ...]
    created_at: float = field(default_factory=time.time)


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    checks: tuple[dict[str, Any], ...]
    missing_evidence: tuple[str, ...]
    conclusion: str


@dataclass(frozen=True)
class BrainPortState:
    name: str
    state: str
    owner: str


def _default_data_dir() -> Path:
    configured = os.getenv("RESEARCH_OS_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    if os.name == "nt":
        return Path(os.getenv("PROGRAMDATA", r"C:\ProgramData")) / "ResearchOS"
    return Path.home() / "ResearchOSData"


def redact_sensitive(value: Any, *, key: str | None = None) -> Any:
    """Return a recursively redacted JSON-compatible value."""
    if key and SENSITIVE_KEY_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {
            str(item_key): redact_sensitive(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [redact_sensitive(item) for item in value]
    return value


class WorkingMemory:
    """Durable, local-first session working memory for Brain Core."""

    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        root = Path(data_dir) if data_dir is not None else _default_data_dir()
        self.root = root / "intelligence"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "working_memory.json"
        self._lock = threading.RLock()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

    def get(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            value = self._read().get(session_id, {})
            return value if isinstance(value, dict) else {}

    def save(self, session_id: str, values: Mapping[str, Any]) -> dict[str, Any]:
        safe_values = redact_sensitive(dict(values))
        with self._lock:
            payload = self._read()
            current = payload.get(session_id, {})
            if not isinstance(current, dict):
                current = {}
            current.update(safe_values)
            current["updated_at"] = time.time()
            payload[session_id] = current
            temp = self.path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.path)
            return dict(current)


class ActivityLedger:
    """Append-only local event ledger with mandatory secret redaction."""

    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        root = Path(data_dir) if data_dir is not None else _default_data_dir()
        self.root = root / "intelligence"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "activity_ledger.jsonl"
        self._lock = threading.RLock()

    def record(
        self,
        event_type: str,
        *,
        session_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": time.time(),
            "payload": redact_sensitive(dict(payload or {})),
        }
        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return event

    def list(self, *, session_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self._lock:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        items: list[dict[str, Any]] = []
        for line in lines:
            try:
                item = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(item, dict):
                continue
            if session_id and item.get("session_id") != session_id:
                continue
            items.append(item)
        return items[-max(1, min(limit, 500)) :]


class CapabilityResolver:
    """Resolve required capabilities against the existing AgentRegistry owner."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self.registry = registry or REGISTRY

    def catalog(self) -> dict[str, list[str]]:
        catalog: dict[str, list[str]] = {}
        for agent in self.registry.list():
            agent_id = str(agent["agent_id"])
            for capability in agent.get("capabilities", []):
                key = str(capability)
                catalog.setdefault(key, []).append(agent_id)
        return {key: sorted(set(value)) for key, value in sorted(catalog.items())}

    def resolve(self, capabilities: Iterable[str]) -> tuple[CapabilityMatch, ...]:
        matches: list[CapabilityMatch] = []
        catalog = self.catalog()
        for capability in capabilities:
            agents = tuple(catalog.get(capability, ()))
            matches.append(CapabilityMatch(capability, agents, bool(agents)))
        return tuple(matches)


_INTENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("debug", ("debug", "error", "fail", "failure", "bug", "แก้", "พัง")),
    ("build", ("build", "compile", "installer", "apk", "exe")),
    ("test", ("test", "verify", "validation", "ตรวจ", "ทดสอบ")),
    ("github", ("github", "workflow", "pull request", "commit", "repo", "ci")),
    ("code", ("code", "coding", "source", "python", "flutter", "dart", "api")),
    ("document", ("document", "pdf", "word", "excel", "sheet", "เอกสาร", "ตาราง")),
    ("shift", ("shift", "roster", "เวร", "คนแทน", "ลา")),
    ("calendar", ("calendar", "ปฏิทิน")),
    ("research", ("research", "ค้น", "วิเคราะห์", "analysis")),
)

_CAPABILITY_MAP: dict[str, tuple[str, ...]] = {
    "debug": ("debug",),
    "build": ("build",),
    "test": ("test",),
    "github": ("github", "workflow"),
    "code": ("code", "architecture"),
    "document": ("document_read",),
    "shift": ("shift", "conflict"),
    "calendar": ("calendar",),
    "research": ("research",),
}


class ResearchOSBrain:
    """Deterministic Brain Core control plane.

    The core provides explicit state, plans, capability resolution, evidence
    checks and observability. A model-backed reasoning adapter can be attached
    later, but the durable control contract remains here.
    """

    def __init__(
        self,
        *,
        registry: AgentRegistry | None = None,
        working_memory: WorkingMemory | None = None,
        ledger: ActivityLedger | None = None,
    ) -> None:
        self.identity = BrainIdentity()
        self.constitution = BrainConstitution()
        self.registry = registry or REGISTRY
        self.capabilities = CapabilityResolver(self.registry)
        self.memory = working_memory or WorkingMemory()
        self.ledger = ledger or ActivityLedger()

    def introspect(self) -> dict[str, Any]:
        catalog = self.capabilities.catalog()
        ports = (
            BrainPortState("agent_registry", "connected", "AgentRegistry"),
            BrainPortState("working_memory", "connected", "Brain Core"),
            BrainPortState("activity_ledger", "connected", "Brain Core"),
            BrainPortState("skill_registry", "connected_via_runtime", "SkillRegistry"),
            BrainPortState("context_engine", "connected_via_runtime", "ContextEngine"),
            BrainPortState("decision_engine", "connected_via_runtime", "DecisionEngine"),
            BrainPortState("tool_registry", "port_ready", "future Tool Registry"),
            BrainPortState("knowledge", "port_ready", "existing Knowledge Engine adapter"),
            BrainPortState("model_gateway", "external", "AI Gateway"),
        )
        return {
            "identity": asdict(self.identity),
            "constitution": asdict(self.constitution),
            "state_machine": [
                "observe",
                "understand",
                "plan",
                "resolve_capabilities",
                "decide",
                "execute",
                "verify",
                "learn",
            ],
            "execution": {
                "direct_tool_execution": False,
                "reason": "Brain Core phase 2 plans, assembles context, evaluates risk and verifies; tool execution is attached later through permissioned ports.",
            },
            "ports": [asdict(item) for item in ports],
            "capability_count": len(catalog),
            "capabilities": catalog,
            "agent_readiness": self.registry.readiness(),
        }

    def understand(
        self,
        objective: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> BrainGoal:
        text = objective.strip()
        if not text:
            raise ValueError("objective is required")
        context = dict(context or {})
        normalized = text.casefold()
        intent = tuple(
            name
            for name, keywords in _INTENT_RULES
            if any(keyword.casefold() in normalized for keyword in keywords)
        ) or ("research",)

        constraints = self._tuple_text(context.get("constraints"))
        known = self._tuple_text(context.get("known"))
        unknown = self._tuple_text(context.get("unknown"))
        definition = self._tuple_text(context.get("definition_of_done"))
        if not definition:
            definition = (
                "requested outcome is produced",
                "verification evidence supports the result",
                "unresolved blockers are reported instead of guessed",
            )

        return BrainGoal(
            goal_id=str(uuid.uuid4()),
            objective=text,
            intent=intent,
            constraints=constraints,
            known=known,
            unknown=unknown,
            definition_of_done=definition,
        )

    def plan(
        self,
        objective: str,
        *,
        session_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> BrainPlan:
        session = (session_id or str(uuid.uuid4())).strip()
        if not session:
            raise ValueError("session_id is required")
        goal = self.understand(objective, context=context)
        required = self._required_capabilities(goal.intent)
        matches = self.capabilities.resolve(required)
        blocked = tuple(
            f"capability unavailable: {match.capability}"
            for match in matches
            if not match.available
        )

        steps: list[BrainPlanStep] = [
            BrainPlanStep(
                "understand",
                "Confirm objective, constraints, known facts and unknowns.",
                "research",
                "Establish an explicit problem statement before action.",
            )
        ]
        dependency = "understand"
        if goal.unknown:
            steps.append(
                BrainPlanStep(
                    "gather_evidence",
                    "Resolve unknowns from authoritative project evidence.",
                    "research",
                    "Unknown information must be verified instead of guessed.",
                    depends_on=(dependency,),
                )
            )
            dependency = "gather_evidence"

        for index, capability in enumerate(required, start=1):
            step_id = f"capability_{index}_{capability.replace('-', '_')}"
            steps.append(
                BrainPlanStep(
                    step_id,
                    f"Apply capability: {capability}.",
                    capability,
                    "Capability was selected from the detected intent.",
                    depends_on=(dependency,),
                )
            )
            dependency = step_id

        steps.append(
            BrainPlanStep(
                "verify",
                "Verify the produced result against definition of done and evidence.",
                "test" if "test" in self.capabilities.catalog() else "research",
                "Completion requires evidence, not an AI assertion.",
                depends_on=(dependency,),
            )
        )

        plan = BrainPlan(
            plan_id=str(uuid.uuid4()),
            session_id=session,
            goal=goal,
            required_capabilities=required,
            capability_matches=matches,
            steps=tuple(steps),
            executable=not blocked,
            blocked_reasons=blocked,
        )
        self.memory.save(
            session,
            {
                "current_goal": asdict(goal),
                "current_plan": asdict(plan),
                "status": "planned",
            },
        )
        self.ledger.record(
            "brain.plan.created",
            session_id=session,
            payload={
                "objective": objective,
                "required_capabilities": required,
                "executable": plan.executable,
                "blocked_reasons": blocked,
                "context": dict(context or {}),
            },
        )
        return plan

    def verify(
        self,
        *,
        session_id: str,
        evidence: Mapping[str, Any],
        required_evidence: Iterable[str],
    ) -> VerificationResult:
        safe_evidence = redact_sensitive(dict(evidence))
        required = tuple(dict.fromkeys(item.strip() for item in required_evidence if item.strip()))
        checks: list[dict[str, Any]] = []
        missing: list[str] = []
        for name in required:
            present = name in safe_evidence and safe_evidence[name] not in (None, "", [], {})
            checks.append({"evidence": name, "present": present})
            if not present:
                missing.append(name)
        verified = not missing
        result = VerificationResult(
            verified=verified,
            checks=tuple(checks),
            missing_evidence=tuple(missing),
            conclusion="verified" if verified else "not_verified",
        )
        self.memory.save(
            session_id,
            {
                "last_verification": asdict(result),
                "status": "verified" if verified else "verification_blocked",
            },
        )
        self.ledger.record(
            "brain.verification.completed",
            session_id=session_id,
            payload={"result": asdict(result), "evidence": safe_evidence},
        )
        return result

    def session(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "working_memory": self.memory.get(session_id),
            "activity": self.ledger.list(session_id=session_id),
        }

    @staticmethod
    def _required_capabilities(intent: Iterable[str]) -> tuple[str, ...]:
        ordered: list[str] = []
        for item in intent:
            for capability in _CAPABILITY_MAP.get(item, ("research",)):
                if capability not in ordered:
                    ordered.append(capability)
        return tuple(ordered or ["research"])

    @staticmethod
    def _tuple_text(value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            text = value.strip()
            return (text,) if text else ()
        if isinstance(value, Iterable):
            result = []
            for item in value:
                text = str(item).strip()
                if text:
                    result.append(text)
            return tuple(dict.fromkeys(result))
        text = str(value).strip()
        return (text,) if text else ()


BRAIN = ResearchOSBrain()
