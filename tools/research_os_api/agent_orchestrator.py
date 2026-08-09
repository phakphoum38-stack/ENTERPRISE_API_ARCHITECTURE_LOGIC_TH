from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from agent_platform import AgentRouter
from agent_runtime import AgentTaskQueue


_FINAL_STEP_STATES = {"completed", "failed", "cancelled"}
_WAITING_STEP_STATES = {"awaiting_confirmation"}
_RECOVERABLE_STEP_STATES = {"planned", "queued", "running", "blocked", "interrupted"}
_TERMINAL_RUN_STATES = {"completed", "failed", "cancelled"}
_MAX_HISTORY_LIMIT = 200
_DEFAULT_MAX_ATTEMPTS = 3
_MAX_ALLOWED_ATTEMPTS = 5


@dataclass
class DelegatedStep:
    step_id: str
    objective: str
    requested_agent: str | None = None
    depends_on: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "planned"
    task_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    attempt_count: int = 0
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    timestamp: float
    run_status: str
    step_id: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationRun:
    run_id: str
    objective: str
    steps: list[DelegatedStep]
    status: str = "planned"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    events: list[AuditEvent] = field(default_factory=list)


class AgentOrchestrator:
    """Coordinates Research OS agents and persists durable orchestration state."""

    def __init__(
        self,
        runtime: AgentTaskQueue | None = None,
        router: AgentRouter | None = None,
        storage_path: str | Path | None = None,
    ) -> None:
        self.runtime = runtime or AgentTaskQueue()
        self.router = router or self.runtime.router
        self._runs: dict[str, OrchestrationRun] = {}
        self.storage_path = self._resolve_storage_path(storage_path)
        self._load_runs()

    @staticmethod
    def _resolve_storage_path(storage_path: str | Path | None) -> Path | None:
        if storage_path is not None:
            return Path(storage_path)
        data_dir = os.environ.get("RESEARCH_OS_DATA_DIR", "").strip()
        if not data_dir:
            return None
        return Path(data_dir) / "agents" / "orchestrations.json"

    def create_run(self, objective: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        objective = objective.strip()
        if not objective:
            raise ValueError("objective is required")
        if not steps:
            raise ValueError("at least one delegated step is required")

        delegated: list[DelegatedStep] = []
        known_ids: set[str] = set()
        for index, item in enumerate(steps, start=1):
            step_id = str(item.get("step_id") or f"step-{index}")
            if step_id in known_ids:
                raise ValueError(f"duplicate step_id: {step_id}")
            known_ids.add(step_id)
            max_attempts = int(item.get("max_attempts", _DEFAULT_MAX_ATTEMPTS))
            if max_attempts < 1 or max_attempts > _MAX_ALLOWED_ATTEMPTS:
                raise ValueError(
                    f"max_attempts for {step_id} must be between 1 and {_MAX_ALLOWED_ATTEMPTS}"
                )
            delegated.append(
                DelegatedStep(
                    step_id=step_id,
                    objective=str(item.get("objective") or "").strip(),
                    requested_agent=item.get("requested_agent"),
                    depends_on=tuple(item.get("depends_on") or ()),
                    context=dict(item.get("context") or {}),
                    max_attempts=max_attempts,
                )
            )

        for step in delegated:
            if not step.objective:
                raise ValueError(f"objective is required for {step.step_id}")
            missing = [dep for dep in step.depends_on if dep not in known_ids]
            if missing:
                raise ValueError(f"unknown dependencies for {step.step_id}: {', '.join(missing)}")

        run = OrchestrationRun(str(uuid.uuid4()), objective, delegated)
        self._runs[run.run_id] = run
        self._record_event(
            run,
            "run.created",
            detail={"step_count": len(delegated)},
        )
        self._persist()
        return self._payload(run)

    def execute(self, run_id: str, confirmed: bool = False) -> dict[str, Any]:
        run = self._require(run_id)
        if run.status == "cancelled":
            raise ValueError("orchestration run is cancelled")

        previous_status = run.status
        run.status = "running"
        run.updated_at = time.time()
        self._record_event(
            run,
            "run.execution_started",
            detail={"confirmed": confirmed, "previous_status": previous_status},
        )
        self._persist()

        while True:
            progressed = False
            for step in run.steps:
                if step.status in _FINAL_STEP_STATES | _WAITING_STEP_STATES:
                    continue
                if step.status == "interrupted":
                    step.status = "planned"
                    step.task_id = None
                    step.error = None
                    self._record_event(run, "step.resumed", step_id=step.step_id)

                dependencies = [self._step(run, dep) for dep in step.depends_on]
                if any(dep.status in {"failed", "cancelled"} for dep in dependencies):
                    step.status = "failed"
                    step.error = "dependency failed or cancelled"
                    progressed = True
                    self._record_event(
                        run,
                        "step.failed",
                        step_id=step.step_id,
                        detail={"error": step.error},
                    )
                    self._persist()
                    continue
                if not all(dep.status == "completed" for dep in dependencies):
                    continue

                if step.attempt_count >= step.max_attempts:
                    step.status = "failed"
                    step.error = "retry limit exhausted"
                    self._record_event(
                        run,
                        "step.retry_exhausted",
                        step_id=step.step_id,
                        detail={
                            "attempt_count": step.attempt_count,
                            "max_attempts": step.max_attempts,
                        },
                    )
                    self._persist()
                    continue

                inherited = {
                    dep.step_id: dep.result for dep in dependencies if dep.result is not None
                }
                context = {
                    **step.context,
                    "orchestration_run_id": run.run_id,
                    "dependency_results": inherited,
                    "attempt": step.attempt_count + 1,
                    "max_attempts": step.max_attempts,
                }
                step.attempt_count += 1
                self._record_event(
                    run,
                    "step.attempt_started",
                    step_id=step.step_id,
                    detail={
                        "attempt": step.attempt_count,
                        "max_attempts": step.max_attempts,
                    },
                )
                task = self.runtime.submit(
                    step.objective,
                    requested_agent=step.requested_agent,
                    context=context,
                    confirmed=confirmed,
                )
                step.task_id = task["task_id"]
                step.status = task["status"]
                step.result = task.get("result")
                step.error = task.get("error")
                run.updated_at = time.time()
                progressed = True
                self._record_event(
                    run,
                    f"step.{step.status}",
                    step_id=step.step_id,
                    detail={
                        "task_id": step.task_id,
                        "requested_agent": step.requested_agent,
                        "error": step.error,
                        "attempt": step.attempt_count,
                        "max_attempts": step.max_attempts,
                    },
                )
                self._persist()

            if not progressed:
                break
            if all(
                step.status in _FINAL_STEP_STATES | _WAITING_STEP_STATES
                for step in run.steps
            ):
                break

        self._refresh_run_status(run)
        self._persist()
        return self._payload(run)

    def confirm(self, run_id: str) -> dict[str, Any]:
        run = self._require(run_id)
        if run.status == "cancelled":
            raise ValueError("orchestration run is cancelled")
        self._record_event(run, "run.confirmation_received")
        for step in run.steps:
            if step.status != "awaiting_confirmation":
                continue

            task = None
            if step.task_id:
                try:
                    task = self.runtime.confirm(step.task_id)
                except ValueError:
                    task = None

            recovered = task is None
            if recovered:
                dependencies = [self._step(run, dep) for dep in step.depends_on]
                inherited = {
                    dep.step_id: dep.result for dep in dependencies if dep.result is not None
                }
                context = {
                    **step.context,
                    "orchestration_run_id": run.run_id,
                    "dependency_results": inherited,
                    "recovered_confirmation": True,
                    "attempt": step.attempt_count,
                    "max_attempts": step.max_attempts,
                }
                task = self.runtime.submit(
                    step.objective,
                    requested_agent=step.requested_agent,
                    context=context,
                    confirmed=True,
                )

            step.task_id = task["task_id"]
            step.status = task["status"]
            step.result = task.get("result")
            step.error = task.get("error")
            run.updated_at = time.time()
            self._record_event(
                run,
                f"step.{step.status}",
                step_id=step.step_id,
                detail={
                    "task_id": step.task_id,
                    "confirmation_recovered": recovered,
                    "error": step.error,
                    "attempt": step.attempt_count,
                    "max_attempts": step.max_attempts,
                },
            )
            self._persist()
        return self.execute(run_id, confirmed=True)

    def retry(self, run_id: str, step_id: str | None = None) -> dict[str, Any]:
        run = self._require(run_id)
        if run.status == "cancelled":
            raise ValueError("orchestration run is cancelled")

        candidates = [self._step(run, step_id)] if step_id else list(run.steps)
        retried = 0
        for step in candidates:
            if step.status != "failed":
                continue
            if step.attempt_count >= step.max_attempts:
                self._record_event(
                    run,
                    "step.retry_rejected",
                    step_id=step.step_id,
                    detail={
                        "reason": "retry limit exhausted",
                        "attempt_count": step.attempt_count,
                        "max_attempts": step.max_attempts,
                    },
                )
                continue
            if step.error and step.error.startswith("dependency failed"):
                dependencies = [self._step(run, dep) for dep in step.depends_on]
                if not all(dep.status == "completed" for dep in dependencies):
                    continue
            step.status = "planned"
            step.task_id = None
            step.result = None
            step.error = None
            retried += 1
            self._record_event(
                run,
                "step.retry_requested",
                step_id=step.step_id,
                detail={
                    "next_attempt": step.attempt_count + 1,
                    "max_attempts": step.max_attempts,
                },
            )

        if retried == 0:
            self._persist()
            raise ValueError("no retryable failed steps")

        run.status = "planned"
        self._persist()
        return self.execute(run_id)

    def cancel(self, run_id: str) -> dict[str, Any]:
        run = self._require(run_id)
        if run.status == "cancelled":
            return self._payload(run)
        if run.status in {"completed", "failed"}:
            raise ValueError(f"cannot cancel terminal orchestration run: {run.status}")

        previous_status = run.status
        for step in run.steps:
            if step.status not in _FINAL_STEP_STATES:
                step.status = "cancelled"
                step.error = "cancelled by request"
                self._record_event(
                    run,
                    "step.cancelled",
                    step_id=step.step_id,
                    detail={"task_id": step.task_id},
                )
        run.status = "cancelled"
        self._record_event(
            run,
            "run.cancelled",
            detail={"from": previous_status},
        )
        self._persist()
        return self._payload(run)

    def get(self, run_id: str) -> dict[str, Any]:
        return self._payload(self._require(run_id))

    def timeline(self, run_id: str) -> list[dict[str, Any]]:
        run = self._require(run_id)
        return [asdict(event) for event in sorted(run.events, key=lambda item: item.timestamp)]

    def list(
        self,
        *,
        status: str | None = None,
        query: str | None = None,
        agent: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if limit is not None and (limit < 1 or limit > _MAX_HISTORY_LIMIT):
            raise ValueError(f"limit must be between 1 and {_MAX_HISTORY_LIMIT}")

        normalized_status = status.strip().casefold() if status else None
        normalized_query = query.strip().casefold() if query else None
        normalized_agent = agent.strip().casefold() if agent else None

        runs = sorted(
            self._runs.values(), key=lambda item: item.created_at, reverse=True
        )
        filtered: list[OrchestrationRun] = []
        for run in runs:
            if normalized_status and run.status.casefold() != normalized_status:
                continue
            if normalized_agent and not any(
                (step.requested_agent or "").casefold() == normalized_agent
                for step in run.steps
            ):
                continue
            if normalized_query:
                searchable = [run.run_id, run.objective]
                searchable.extend(step.step_id for step in run.steps)
                searchable.extend(step.objective for step in run.steps)
                if not any(normalized_query in value.casefold() for value in searchable):
                    continue
            filtered.append(run)
            if limit is not None and len(filtered) >= limit:
                break

        return [self._payload(run) for run in filtered]

    def _refresh_run_status(self, run: OrchestrationRun) -> None:
        previous_status = run.status
        statuses = {step.status for step in run.steps}
        if "cancelled" in statuses and statuses <= {"completed", "cancelled"}:
            run.status = "cancelled"
        elif "failed" in statuses:
            run.status = "failed"
        elif "awaiting_confirmation" in statuses:
            run.status = "awaiting_confirmation"
        elif statuses == {"completed"}:
            run.status = "completed"
        elif "interrupted" in statuses:
            run.status = "interrupted"
        else:
            run.status = "blocked"
        run.updated_at = time.time()
        if run.status != previous_status:
            self._record_event(
                run,
                "run.status_changed",
                detail={"from": previous_status, "to": run.status},
            )

    def _load_runs(self) -> None:
        if self.storage_path is None or not self.storage_path.exists():
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"failed to load orchestration state: {self.storage_path}"
            ) from exc

        raw_runs = payload.get("runs", []) if isinstance(payload, dict) else []
        recovered_any = False
        for item in raw_runs:
            steps = []
            for raw_step in item.get("steps", []):
                status = str(raw_step.get("status") or "planned")
                if status in _RECOVERABLE_STEP_STATES and status != "planned":
                    status = "interrupted"
                    recovered_any = True
                max_attempts = int(raw_step.get("max_attempts", _DEFAULT_MAX_ATTEMPTS))
                max_attempts = max(1, min(max_attempts, _MAX_ALLOWED_ATTEMPTS))
                steps.append(
                    DelegatedStep(
                        step_id=str(raw_step.get("step_id") or ""),
                        objective=str(raw_step.get("objective") or ""),
                        requested_agent=raw_step.get("requested_agent"),
                        depends_on=tuple(raw_step.get("depends_on") or ()),
                        context=dict(raw_step.get("context") or {}),
                        status=status,
                        task_id=raw_step.get("task_id"),
                        result=raw_step.get("result"),
                        error=raw_step.get("error"),
                        attempt_count=max(0, int(raw_step.get("attempt_count", 0))),
                        max_attempts=max_attempts,
                    )
                )
            events = [
                AuditEvent(
                    event_id=str(raw_event.get("event_id") or uuid.uuid4()),
                    event_type=str(raw_event.get("event_type") or "run.legacy_event"),
                    timestamp=float(raw_event.get("timestamp") or time.time()),
                    run_status=str(raw_event.get("run_status") or item.get("status") or "planned"),
                    step_id=raw_event.get("step_id"),
                    detail=dict(raw_event.get("detail") or {}),
                )
                for raw_event in item.get("events", [])
                if isinstance(raw_event, dict)
            ]
            run = OrchestrationRun(
                run_id=str(item.get("run_id") or ""),
                objective=str(item.get("objective") or ""),
                steps=steps,
                status=str(item.get("status") or "planned"),
                created_at=float(item.get("created_at") or time.time()),
                updated_at=float(item.get("updated_at") or time.time()),
                events=events,
            )
            if run.status not in _TERMINAL_RUN_STATES and (
                run.status in {"running", "blocked"}
                or any(step.status == "interrupted" for step in run.steps)
            ):
                previous_status = run.status
                run.status = "interrupted"
                recovered_any = True
                self._record_event(
                    run,
                    "run.recovered_after_restart",
                    detail={"from": previous_status, "to": "interrupted"},
                )
            if run.run_id:
                self._runs[run.run_id] = run

        if recovered_any or raw_runs:
            self._persist()

    def _persist(self) -> None:
        if self.storage_path is None:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 2,
            "updated_at": time.time(),
            "runs": [
                self._payload(run)
                for run in sorted(self._runs.values(), key=lambda item: item.created_at)
            ],
        }
        temporary = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.storage_path)

    def _record_event(
        self,
        run: OrchestrationRun,
        event_type: str,
        *,
        step_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        run.events.append(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                timestamp=time.time(),
                run_status=run.status,
                step_id=step_id,
                detail=dict(detail or {}),
            )
        )
        run.updated_at = time.time()

    def _require(self, run_id: str) -> OrchestrationRun:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise ValueError(f"unknown orchestration run: {run_id}") from exc

    @staticmethod
    def _step(run: OrchestrationRun, step_id: str) -> DelegatedStep:
        for step in run.steps:
            if step.step_id == step_id:
                return step
        raise ValueError(f"unknown step: {step_id}")

    @staticmethod
    def _payload(run: OrchestrationRun) -> dict[str, Any]:
        return asdict(run)


ORCHESTRATOR = AgentOrchestrator()
