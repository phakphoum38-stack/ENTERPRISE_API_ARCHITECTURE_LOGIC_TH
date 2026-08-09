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


_FINAL_STEP_STATES = {"completed", "failed"}
_WAITING_STEP_STATES = {"awaiting_confirmation"}
_RECOVERABLE_STEP_STATES = {"planned", "queued", "running", "blocked", "interrupted"}


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


@dataclass
class OrchestrationRun:
    run_id: str
    objective: str
    steps: list[DelegatedStep]
    status: str = "planned"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


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
            delegated.append(
                DelegatedStep(
                    step_id=step_id,
                    objective=str(item.get("objective") or "").strip(),
                    requested_agent=item.get("requested_agent"),
                    depends_on=tuple(item.get("depends_on") or ()),
                    context=dict(item.get("context") or {}),
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
        self._persist()
        return self._payload(run)

    def execute(self, run_id: str, confirmed: bool = False) -> dict[str, Any]:
        run = self._require(run_id)
        run.status = "running"
        run.updated_at = time.time()
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

                dependencies = [self._step(run, dep) for dep in step.depends_on]
                if any(dep.status == "failed" for dep in dependencies):
                    step.status = "failed"
                    step.error = "dependency failed"
                    progressed = True
                    self._persist()
                    continue
                if not all(dep.status == "completed" for dep in dependencies):
                    continue

                inherited = {
                    dep.step_id: dep.result for dep in dependencies if dep.result is not None
                }
                context = {
                    **step.context,
                    "orchestration_run_id": run.run_id,
                    "dependency_results": inherited,
                }
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
        for step in run.steps:
            if step.status != "awaiting_confirmation":
                continue

            task = None
            if step.task_id:
                try:
                    task = self.runtime.confirm(step.task_id)
                except ValueError:
                    task = None

            if task is None:
                dependencies = [self._step(run, dep) for dep in step.depends_on]
                inherited = {
                    dep.step_id: dep.result for dep in dependencies if dep.result is not None
                }
                context = {
                    **step.context,
                    "orchestration_run_id": run.run_id,
                    "dependency_results": inherited,
                    "recovered_confirmation": True,
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
            self._persist()
        return self.execute(run_id, confirmed=True)

    def get(self, run_id: str) -> dict[str, Any]:
        return self._payload(self._require(run_id))

    def list(self) -> list[dict[str, Any]]:
        return [
            self._payload(run)
            for run in sorted(
                self._runs.values(), key=lambda item: item.created_at, reverse=True
            )
        ]

    def _refresh_run_status(self, run: OrchestrationRun) -> None:
        statuses = {step.status for step in run.steps}
        if "failed" in statuses:
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
        for item in raw_runs:
            steps = []
            for raw_step in item.get("steps", []):
                status = str(raw_step.get("status") or "planned")
                if status in _RECOVERABLE_STEP_STATES and status != "planned":
                    status = "interrupted"
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
                    )
                )
            run = OrchestrationRun(
                run_id=str(item.get("run_id") or ""),
                objective=str(item.get("objective") or ""),
                steps=steps,
                status=str(item.get("status") or "planned"),
                created_at=float(item.get("created_at") or time.time()),
                updated_at=float(item.get("updated_at") or time.time()),
            )
            if run.status in {"running", "blocked"} or any(
                step.status == "interrupted" for step in run.steps
            ):
                run.status = "interrupted"
            if run.run_id:
                self._runs[run.run_id] = run

        self._persist()

    def _persist(self) -> None:
        if self.storage_path is None:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
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
