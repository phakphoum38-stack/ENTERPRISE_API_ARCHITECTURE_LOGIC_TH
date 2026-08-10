#!/usr/bin/env python3
"""Governed end-to-end task runner for Research OS AI Brain.

Phase 8 connects the existing Brain plan, AgentOrchestrator, SkillRegistry,
SkillExecutor, hardened ExecutionController and evidence verifier without
creating a second task graph or a direct tool bypass.

The AgentOrchestrator remains the canonical dependency graph. This runner stores
only task-to-plan bindings and verified execution evidence keyed by the
orchestration run id. Raw secrets are never accepted into durable task bindings;
secret-bearing values must be supplied ephemerally at execution time and are
handled by the existing secret-aware execution boundary.
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

from agent_orchestrator import AgentOrchestrator, ORCHESTRATOR
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory
from v2_secret_redactor import discover_secret_values, sanitize_request_fields
from v2_skill_executor import SkillExecutionRequest, SkillExecutor
from v2_skill_registry import SkillRegistry


GOVERNED_TASK_CONTRACT = "brain-governed-task-runner-phase-8"
_TASK_SCHEMA_VERSION = 1
_TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{2,127}$", re.IGNORECASE)
_TERMINAL_TASK_STATES = {"verified", "failed", "blocked", "cancelled", "verification_failed"}


@dataclass(frozen=True)
class GovernedTaskBinding:
    capability: str
    skill_id: str
    action: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    granted_permissions: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)
    tool_id: str | None = None
    dry_run: bool = False


class GovernedTaskStore:
    """Durable task binding/evidence store; the orchestration DAG stays external."""

    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        if data_dir is None:
            configured = os.environ.get("RESEARCH_OS_DATA_DIR", "").strip()
            if configured:
                root = Path(configured)
            elif os.name == "nt":
                root = Path(os.getenv("PROGRAMDATA", r"C:\\ProgramData")) / "ResearchOS"
            else:
                root = Path.home() / "ResearchOSData"
        else:
            root = Path(data_dir)
        self.root = root / "intelligence"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "governed_tasks.json"
        self._lock = threading.RLock()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": _TASK_SCHEMA_VERSION, "tasks": {}}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {"schema_version": _TASK_SCHEMA_VERSION, "tasks": {}}
        tasks = raw.get("tasks") if isinstance(raw, dict) else None
        return {
            "schema_version": _TASK_SCHEMA_VERSION,
            "tasks": tasks if isinstance(tasks, dict) else {},
        }

    def _write(self, payload: Mapping[str, Any]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def save(self, task_id: str, values: Mapping[str, Any]) -> dict[str, Any]:
        safe = sanitize_request_fields(dict(values))
        with self._lock:
            payload = self._read()
            current = payload["tasks"].get(task_id, {})
            if not isinstance(current, dict):
                current = {}
            current.update(safe)
            current["task_id"] = task_id
            current["updated_at"] = time.time()
            payload["tasks"][task_id] = current
            self._write(payload)
            return dict(current)

    def get(self, task_id: str) -> dict[str, Any]:
        with self._lock:
            value = self._read()["tasks"].get(task_id)
            if not isinstance(value, dict):
                raise ValueError(f"unknown governed task: {task_id}")
            return dict(value)

    def list(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        with self._lock:
            tasks = [dict(item) for item in self._read()["tasks"].values() if isinstance(item, dict)]
        if status:
            normalized = status.casefold().strip()
            tasks = [item for item in tasks if str(item.get("status", "")).casefold() == normalized]
        return sorted(tasks, key=lambda item: float(item.get("created_at", 0.0)), reverse=True)[:limit]


class GovernedTaskRunner:
    """Connect Brain planning to agent delegation and verified Skill -> Tool work."""

    def __init__(
        self,
        *,
        brain: ResearchOSBrain,
        skills: SkillRegistry,
        skill_execution: SkillExecutor,
        orchestrator: AgentOrchestrator | None = None,
        store: GovernedTaskStore | None = None,
        ledger: ActivityLedger | None = None,
    ) -> None:
        self.brain = brain
        self.skills = skills
        self.skill_execution = skill_execution
        self.orchestrator = orchestrator or ORCHESTRATOR
        self.store = store or GovernedTaskStore(self.brain.memory.root.parent)
        self.ledger = ledger or self.brain.ledger
        self._lock = threading.RLock()

    @staticmethod
    def _safe_text(value: str, *, field_name: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError(f"{field_name} is required")
        safe = sanitize_request_fields(text)
        if safe != text:
            raise ValueError(f"{field_name} contains credential-like material")
        return text

    @staticmethod
    def _normalize_mapping(value: Mapping[str, Any] | None, *, field_name: str) -> dict[str, Any]:
        raw = dict(value or {})
        safe = sanitize_request_fields(raw)
        if safe != raw:
            raise ValueError(
                f"raw secret material is not accepted in durable {field_name}; use ephemeral execution input or Credential Broker"
            )
        return raw

    @staticmethod
    def _normalize_permissions(values: Iterable[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.strip() for item in values if item.strip()))

    def _normalize_bindings(
        self,
        bindings: Iterable[GovernedTaskBinding | Mapping[str, Any]],
    ) -> dict[str, GovernedTaskBinding]:
        normalized: dict[str, GovernedTaskBinding] = {}
        for item in bindings:
            if isinstance(item, GovernedTaskBinding):
                raw = asdict(item)
            elif isinstance(item, Mapping):
                raw = dict(item)
            else:
                raise TypeError("governed task binding must be a mapping or GovernedTaskBinding")
            capability = self._safe_text(str(raw.get("capability") or ""), field_name="capability")
            if capability in normalized:
                raise ValueError(f"duplicate governed task capability binding: {capability}")
            skill_id = self._safe_text(str(raw.get("skill_id") or ""), field_name="skill_id")
            action = self._safe_text(str(raw.get("action") or ""), field_name="action")
            payload = self._normalize_mapping(raw.get("payload") if isinstance(raw.get("payload"), Mapping) else {}, field_name="task payload")
            evidence = self._normalize_mapping(raw.get("evidence") if isinstance(raw.get("evidence"), Mapping) else {}, field_name="task evidence")
            tool_id_value = raw.get("tool_id")
            tool_id = str(tool_id_value).strip() if tool_id_value is not None else None
            if tool_id:
                self._safe_text(tool_id, field_name="tool_id")
            permissions = self._normalize_permissions(raw.get("granted_permissions") or ())
            normalized[capability] = GovernedTaskBinding(
                capability=capability,
                skill_id=skill_id,
                action=action,
                payload=payload,
                granted_permissions=permissions,
                evidence=evidence,
                tool_id=tool_id or None,
                dry_run=bool(raw.get("dry_run", False)),
            )
        return normalized

    def prepare(
        self,
        objective: str,
        *,
        session_id: str,
        bindings: Iterable[GovernedTaskBinding | Mapping[str, Any]],
        context: Mapping[str, Any] | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        safe_objective = self._safe_text(objective, field_name="objective")
        safe_session = self._safe_text(session_id, field_name="session_id")
        safe_context = self._normalize_mapping(context, field_name="task context")
        normalized_bindings = self._normalize_bindings(bindings)
        task = (task_id or str(uuid.uuid4())).strip()
        if not _TASK_ID_RE.fullmatch(task):
            raise ValueError("invalid governed task_id")

        plan = self.brain.plan(safe_objective, session_id=safe_session, context=safe_context)
        match_by_capability = {item.capability: item for item in plan.capability_matches}
        blocked: list[str] = list(plan.blocked_reasons)
        execution_bindings: list[dict[str, Any]] = []
        orchestration_steps: list[dict[str, Any]] = []
        previous_step_id: str | None = None

        for index, capability in enumerate(plan.required_capabilities, start=1):
            binding = normalized_bindings.get(capability)
            if binding is None:
                blocked.append(f"missing skill/action binding for capability: {capability}")
                continue

            try:
                skill = self.skills.get(binding.skill_id)
                skill_state = self.skills.describe(binding.skill_id)
            except ValueError as exc:
                blocked.append(str(exc))
                continue
            if not skill_state["ready"]:
                blocked.append(f"skill not ready: {binding.skill_id}")
                continue
            if capability.casefold() not in {item.casefold() for item in skill.capabilities}:
                blocked.append(
                    f"skill {binding.skill_id} does not provide required capability: {capability}"
                )
                continue

            missing_permissions = [
                permission
                for permission in skill.permissions
                if permission.casefold() not in {item.casefold() for item in binding.granted_permissions}
            ]
            blocked.extend(
                f"skill permission missing for {binding.skill_id}: {permission}"
                for permission in missing_permissions
            )

            tool_match = self.skill_execution.resolve_tool(
                skill,
                requested_tool_id=binding.tool_id,
            )
            if not tool_match.get("matched"):
                blocked.extend(
                    f"{binding.skill_id}: {reason}"
                    for reason in tool_match.get("blocked_reasons", ())
                )

            capability_match = match_by_capability.get(capability)
            agents = tuple(capability_match.agents) if capability_match else ()
            if not agents:
                blocked.append(f"no ready agent for capability: {capability}")
                continue

            step_id = f"task-{index}-{re.sub(r'[^a-zA-Z0-9_.-]+', '-', capability).strip('-') or 'capability'}"
            execution_bindings.append(
                {
                    "step_id": step_id,
                    "capability": capability,
                    "skill_id": binding.skill_id,
                    "action": binding.action,
                    "payload": dict(binding.payload),
                    "granted_permissions": list(binding.granted_permissions),
                    "evidence": dict(binding.evidence),
                    "tool_id": binding.tool_id,
                    "dry_run": binding.dry_run,
                    "requested_agent": agents[0],
                    "tool_match": tool_match,
                }
            )
            orchestration_steps.append(
                {
                    "step_id": step_id,
                    "objective": f"{capability}: {safe_objective}",
                    "requested_agent": agents[0],
                    "depends_on": [previous_step_id] if previous_step_id else [],
                    # Never persist tool payloads or evidence in AgentOrchestrator.
                    "context": {
                        "governed_task_contract": GOVERNED_TASK_CONTRACT,
                        "governed_task_id": task,
                        "brain_session_id": safe_session,
                        "capability": capability,
                        "skill_id": binding.skill_id,
                    },
                }
            )
            previous_step_id = step_id

        record = {
            "contract": GOVERNED_TASK_CONTRACT,
            "task_id": task,
            "session_id": safe_session,
            "objective": safe_objective,
            "status": "blocked" if blocked else "prepared",
            "blocked_reasons": list(dict.fromkeys(blocked)),
            "brain_plan": asdict(plan),
            "bindings": execution_bindings,
            "step_results": {},
            "orchestration_run_id": None,
            "pending_step_id": None,
            "final_verification": None,
            "created_at": time.time(),
        }

        if not blocked:
            run = self.orchestrator.create_run(safe_objective, orchestration_steps)
            record["orchestration_run_id"] = run["run_id"]

        saved = self.store.save(task, record)
        self.ledger.record(
            "brain.governed_task.prepared",
            session_id=safe_session,
            payload={
                "task_id": task,
                "orchestration_run_id": saved.get("orchestration_run_id"),
                "status": saved["status"],
                "capabilities": list(plan.required_capabilities),
                "blocked_reasons": saved.get("blocked_reasons", []),
            },
        )
        return self.get(task)

    def start(
        self,
        task_id: str,
        *,
        ephemeral_inputs: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            record = self.store.get(task_id)
            if record["status"] in _TERMINAL_TASK_STATES:
                return self.get(task_id)
            run_id = str(record.get("orchestration_run_id") or "")
            if not run_id:
                raise ValueError("governed task has no orchestration run")

            run = self.orchestrator.get(run_id)
            if run["status"] == "awaiting_confirmation":
                self.store.save(task_id, {"status": "awaiting_agent_confirmation"})
                return self.get(task_id)
            if run["status"] not in {"completed", "failed", "cancelled"}:
                run = self.orchestrator.execute(run_id)

            if run["status"] == "awaiting_confirmation":
                self.store.save(task_id, {"status": "awaiting_agent_confirmation"})
                return self.get(task_id)
            if run["status"] in {"failed", "cancelled"}:
                status = "cancelled" if run["status"] == "cancelled" else "failed"
                self.store.save(task_id, {"status": status, "orchestration_status": run["status"]})
                self.ledger.record(
                    "brain.governed_task.agent_orchestration_stopped",
                    session_id=str(record["session_id"]),
                    payload={"task_id": task_id, "orchestration_status": run["status"]},
                )
                return self.get(task_id)

            self.store.save(task_id, {"status": "executing", "orchestration_status": run["status"]})
            return self._execute_skill_steps(
                task_id,
                approved_step_id=None,
                ephemeral_inputs=ephemeral_inputs or {},
            )

    def approve_step(
        self,
        task_id: str,
        step_id: str,
        *,
        ephemeral_input: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            record = self.store.get(task_id)
            bindings = {item["step_id"]: item for item in record.get("bindings", [])}
            if step_id not in bindings:
                raise ValueError(f"unknown governed task step: {step_id}")
            pending = self._first_unverified_step(record)
            if pending and pending != step_id:
                raise ValueError(f"approval must target next pending step: {pending}")

            run_id = str(record.get("orchestration_run_id") or "")
            run = self.orchestrator.get(run_id)
            if run["status"] == "awaiting_confirmation":
                run = self.orchestrator.confirm(run_id)
            if run["status"] != "completed":
                self.store.save(
                    task_id,
                    {"status": "awaiting_agent_confirmation", "orchestration_status": run["status"]},
                )
                return self.get(task_id)

            self.ledger.record(
                "brain.governed_task.step_approval_received",
                session_id=str(record["session_id"]),
                payload={"task_id": task_id, "step_id": step_id},
            )
            return self._execute_skill_steps(
                task_id,
                approved_step_id=step_id,
                ephemeral_inputs={step_id: dict(ephemeral_input or {})},
            )

    def _execute_skill_steps(
        self,
        task_id: str,
        *,
        approved_step_id: str | None,
        ephemeral_inputs: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        record = self.store.get(task_id)
        step_results = dict(record.get("step_results") or {})
        session_id = str(record["session_id"])

        for binding in record.get("bindings", []):
            step_id = str(binding["step_id"])
            existing = step_results.get(step_id)
            if isinstance(existing, Mapping) and existing.get("status") == "verified":
                continue

            if approved_step_id and step_id != approved_step_id:
                self.store.save(task_id, {"status": "awaiting_approval", "pending_step_id": step_id})
                return self.get(task_id)

            ephemeral = dict(ephemeral_inputs.get(step_id) or {})
            secret_values = discover_secret_values(ephemeral)
            payload = {**dict(binding.get("payload") or {}), **ephemeral}
            result = self.skill_execution.execute(
                SkillExecutionRequest(
                    session_id=session_id,
                    skill_id=str(binding["skill_id"]),
                    action=str(binding["action"]),
                    payload=payload,
                    granted_permissions=tuple(binding.get("granted_permissions") or ()),
                    evidence=dict(binding.get("evidence") or {}),
                    approved=bool(approved_step_id == step_id),
                    dry_run=bool(binding.get("dry_run", False)),
                    tool_id=str(binding["tool_id"]) if binding.get("tool_id") else None,
                    idempotency_key=f"{task_id}:{step_id}",
                    correlation_id=task_id,
                    secret_values=secret_values,
                )
            )
            result_payload = asdict(result)
            step_results[step_id] = result_payload
            self.store.save(task_id, {"step_results": step_results})

            self.ledger.record(
                "brain.governed_task.skill_step_observed",
                session_id=session_id,
                payload={
                    "task_id": task_id,
                    "step_id": step_id,
                    "skill_id": binding["skill_id"],
                    "tool_id": result.selected_tool_id,
                    "status": result.status,
                },
            )

            if result.status == "awaiting_approval":
                self.store.save(
                    task_id,
                    {"status": "awaiting_approval", "pending_step_id": step_id},
                )
                return self.get(task_id)
            if result.status != "verified":
                state = "blocked" if result.status == "blocked" else (
                    "verification_failed" if result.status == "verification_failed" else "failed"
                )
                self.store.save(
                    task_id,
                    {
                        "status": state,
                        "pending_step_id": step_id,
                        "blocked_reasons": list(result.blocked_reasons),
                    },
                )
                return self.get(task_id)

            self.store.save(task_id, {"pending_step_id": None, "status": "executing"})
            approved_step_id = None

        verified_steps = [
            step_id
            for step_id, result in step_results.items()
            if isinstance(result, Mapping) and result.get("status") == "verified"
        ]
        final = self.brain.verify(
            session_id=session_id,
            evidence={
                "orchestration_status": "completed",
                "verified_skill_steps": verified_steps,
                "governed_task_id": task_id,
            },
            required_evidence=("orchestration_status", "verified_skill_steps"),
        )
        final_payload = asdict(final)
        status = "verified" if final.verified else "verification_failed"
        self.store.save(
            task_id,
            {
                "status": status,
                "pending_step_id": None,
                "final_verification": final_payload,
                "verified_step_count": len(verified_steps),
            },
        )
        self.ledger.record(
            "brain.governed_task.completed",
            session_id=session_id,
            payload={
                "task_id": task_id,
                "status": status,
                "verified_step_count": len(verified_steps),
                "final_verification": final_payload,
            },
        )
        return self.get(task_id)

    @staticmethod
    def _first_unverified_step(record: Mapping[str, Any]) -> str | None:
        results = record.get("step_results") if isinstance(record.get("step_results"), Mapping) else {}
        for binding in record.get("bindings", []):
            step_id = str(binding.get("step_id") or "")
            result = results.get(step_id) if isinstance(results, Mapping) else None
            if not isinstance(result, Mapping) or result.get("status") != "verified":
                return step_id or None
        return None

    def cancel(self, task_id: str) -> dict[str, Any]:
        with self._lock:
            record = self.store.get(task_id)
            if record["status"] == "cancelled":
                return self.get(task_id)
            run_id = str(record.get("orchestration_run_id") or "")
            if run_id:
                run = self.orchestrator.get(run_id)
                if run["status"] not in {"completed", "failed", "cancelled"}:
                    self.orchestrator.cancel(run_id)
            self.store.save(task_id, {"status": "cancelled", "pending_step_id": None})
            self.ledger.record(
                "brain.governed_task.cancelled",
                session_id=str(record["session_id"]),
                payload={"task_id": task_id},
            )
            return self.get(task_id)

    def get(self, task_id: str) -> dict[str, Any]:
        record = self.store.get(task_id)
        run_id = str(record.get("orchestration_run_id") or "")
        orchestration = self.orchestrator.get(run_id) if run_id else None
        return {
            **record,
            "orchestration": orchestration,
        }

    def timeline(self, task_id: str) -> dict[str, Any]:
        record = self.store.get(task_id)
        run_id = str(record.get("orchestration_run_id") or "")
        return {
            "task_id": task_id,
            "orchestration": self.orchestrator.timeline(run_id) if run_id else [],
            "brain_activity": [
                item
                for item in self.ledger.list(session_id=str(record["session_id"]), limit=500)
                if item.get("payload", {}).get("task_id") == task_id
            ],
        }

    def list(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.store.list(status=status, limit=limit)

    def dashboard(self) -> dict[str, Any]:
        tasks = self.store.list(limit=500)
        return {
            "contract": GOVERNED_TASK_CONTRACT,
            "canonical_dependency_graph": "AgentOrchestrator",
            "agent_selection": "Brain capability match -> AgentRegistry",
            "skill_execution": "SkillExecutor",
            "tool_execution": "HardenedExecutionController only",
            "approval_scope": "one pending skill step at a time",
            "raw_secret_persistence": False,
            "unrestricted_shell": False,
            "task_count": len(tasks),
            "verified": sum(1 for item in tasks if item.get("status") == "verified"),
            "awaiting_approval": sum(
                1 for item in tasks if item.get("status") in {"awaiting_approval", "awaiting_agent_confirmation"}
            ),
            "failed": sum(
                1 for item in tasks if item.get("status") in {"failed", "verification_failed", "blocked"}
            ),
        }
