from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from agent_platform import AgentRouter
from agent_runtime import AgentTaskQueue


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
    """Coordinates multiple Research OS agents without bypassing runtime policy."""

    def __init__(self, runtime: AgentTaskQueue | None = None, router: AgentRouter | None = None) -> None:
        self.runtime = runtime or AgentTaskQueue()
        self.router = router or self.runtime.router
        self._runs: dict[str, OrchestrationRun] = {}

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
        return self._payload(run)

    def execute(self, run_id: str, confirmed: bool = False) -> dict[str, Any]:
        run = self._require(run_id)
        run.status = "running"
        run.updated_at = time.time()

        while True:
            progressed = False
            for step in run.steps:
                if step.status in {"completed", "awaiting_confirmation", "failed"}:
                    continue
                dependencies = [self._step(run, dep) for dep in step.depends_on]
                if any(dep.status == "failed" for dep in dependencies):
                    step.status = "failed"
                    step.error = "dependency failed"
                    progressed = True
                    continue
                if not all(dep.status == "completed" for dep in dependencies):
                    continue

                inherited = {
                    dep.step_id: dep.result for dep in dependencies if dep.result is not None
                }
                context = {**step.context, "orchestration_run_id": run.run_id, "dependency_results": inherited}
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
                progressed = True

            if not progressed:
                break
            if all(step.status in {"completed", "awaiting_confirmation", "failed"} for step in run.steps):
                break

        statuses = {step.status for step in run.steps}
        if "failed" in statuses:
            run.status = "failed"
        elif "awaiting_confirmation" in statuses:
            run.status = "awaiting_confirmation"
        elif statuses == {"completed"}:
            run.status = "completed"
        else:
            run.status = "blocked"
        run.updated_at = time.time()
        return self._payload(run)

    def confirm(self, run_id: str) -> dict[str, Any]:
        run = self._require(run_id)
        for step in run.steps:
            if step.status == "awaiting_confirmation" and step.task_id:
                task = self.runtime.confirm(step.task_id)
                step.status = task["status"]
                step.result = task.get("result")
                step.error = task.get("error")
        return self.execute(run_id, confirmed=True)

    def get(self, run_id: str) -> dict[str, Any]:
        return self._payload(self._require(run_id))

    def list(self) -> list[dict[str, Any]]:
        return [self._payload(run) for run in sorted(self._runs.values(), key=lambda item: item.created_at, reverse=True)]

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
