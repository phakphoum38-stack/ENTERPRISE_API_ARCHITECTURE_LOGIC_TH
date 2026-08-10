from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from agent_platform import ROUTER, AgentRouter
from brain_skills import BRAIN
from v2_completion_crew import register_completion_crew


@dataclass
class AgentEvent:
    event_id: str
    event_type: str
    task_id: str
    agent_id: str | None
    timestamp: float
    correlation_id: str | None = None
    run_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeTask:
    task_id: str
    objective: str
    requested_agent: str | None
    context: dict[str, Any]
    status: str
    selected_agent: str | None = None
    route_reason: str | None = None
    requires_confirmation: bool = False
    confirmed: bool = False
    correlation_id: str | None = None
    run_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class AgentEventBus:
    def __init__(self, max_events: int = 500) -> None:
        self._max_events = max_events
        self._events: list[AgentEvent] = []
        self._lock = threading.RLock()

    def publish(
        self,
        event_type: str,
        task_id: str,
        agent_id: str | None = None,
        *,
        correlation_id: str | None = None,
        run_id: str | None = None,
        **payload: Any,
    ) -> AgentEvent:
        event = AgentEvent(
            str(uuid.uuid4()),
            event_type,
            task_id,
            agent_id,
            time.time(),
            correlation_id,
            run_id,
            payload,
        )
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]
        return event

    def list(self, task_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            items = self._events
            if task_id:
                items = [item for item in items if item.task_id == task_id]
            return [asdict(item) for item in items[-max(1, min(limit, 500)):]]


class SharedContextStore:
    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        root = Path(data_dir or os.environ.get("RESEARCH_OS_DATA_DIR") or Path.home() / "ResearchOSData")
        self.root = root / "agents"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "shared_context.json"
        self._lock = threading.RLock()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

    def get(self, scope: str) -> dict[str, Any]:
        with self._lock:
            value = self._read().get(scope, {})
            return value if isinstance(value, dict) else {}

    def merge(self, scope: str, values: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            payload = self._read()
            current = payload.get(scope, {})
            if not isinstance(current, dict):
                current = {}
            current.update(values)
            payload[scope] = current
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return current


class AgentTaskQueue:
    def __init__(self, router: AgentRouter | None = None, event_bus: AgentEventBus | None = None, context_store: SharedContextStore | None = None) -> None:
        self.router = router or ROUTER
        self.events = event_bus or AgentEventBus()
        self.context_store = context_store or SharedContextStore()
        self._tasks: dict[str, RuntimeTask] = {}
        self._lock = threading.RLock()

    def submit(self, objective: str, requested_agent: str | None = None, context: dict[str, Any] | None = None, confirmed: bool = False) -> dict[str, Any]:
        objective = objective.strip()
        if not objective:
            raise ValueError("objective is required")
        route = self.router.route(objective, requested_agent=requested_agent)
        agent = route["agent"]
        task_id = str(uuid.uuid4())
        task_context = dict(context or {})
        run_id = self._text(task_context.get("orchestration_run_id"))
        correlation = self._text(task_context.get("correlation_id")) or run_id or task_id
        task = RuntimeTask(
            task_id=task_id,
            objective=objective,
            requested_agent=requested_agent,
            context=task_context,
            status="queued",
            selected_agent=str(agent["agent_id"]),
            route_reason=str(route["reason"]),
            requires_confirmation=bool(route["requires_confirmation_for_writes"]),
            confirmed=confirmed,
            correlation_id=correlation,
            run_id=run_id,
        )
        with self._lock:
            self._tasks[task.task_id] = task
        self._publish(task, "task.queued", objective=objective)
        return self.execute(task.task_id)

    def confirm(self, task_id: str) -> dict[str, Any]:
        task = self._require(task_id)
        task.confirmed = True
        task.updated_at = time.time()
        self._publish(task, "task.confirmed")
        return self.execute(task_id)

    def execute(self, task_id: str) -> dict[str, Any]:
        task = self._require(task_id)
        if task.requires_confirmation and not task.confirmed:
            task.status = "awaiting_confirmation"
            task.updated_at = time.time()
            self._publish(task, "task.awaiting_confirmation")
            return self._task_payload(task)

        task.status = "running"
        task.updated_at = time.time()
        self._publish(task, "task.started")
        try:
            shared = self.context_store.get(f"shared:{task.selected_agent}")
            merged_context = {**shared, **task.context}
            brain_plan = BRAIN.plan(
                task.objective,
                complexity_level=self._optional_int(
                    merged_context.get("brain_complexity_level")
                ),
                requested_workers=self._optional_int(
                    merged_context.get("brain_requested_workers")
                ),
                budget_workers=self._optional_int(
                    merged_context.get("brain_budget_workers")
                ),
                ready_workers=self._optional_int(
                    merged_context.get("brain_ready_workers")
                ),
            )
            task.result = {
                "agent_id": task.selected_agent,
                "objective": task.objective,
                "context": merged_context,
                "execution": "runtime_ready",
                "correlation_id": task.correlation_id,
                "run_id": task.run_id,
                "brain_plan": brain_plan,
                "note": "Agent Runtime 2.0 dispatch is active with shared dynamic registry, adaptive Brain Skills planning and readiness-aware routing.",
            }
            task.status = "completed"
            task.updated_at = time.time()
            self.context_store.merge(
                f"shared:{task.selected_agent}",
                {
                    "last_task_id": task.task_id,
                    "last_objective": task.objective,
                    "last_correlation_id": task.correlation_id,
                    "last_run_id": task.run_id,
                },
            )
            self._publish(task, "task.completed")
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            task.updated_at = time.time()
            self._publish(task, "task.failed", error=str(exc))
        return self._task_payload(task)

    def get(self, task_id: str) -> dict[str, Any]:
        return self._task_payload(self._require(task_id))

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._task_payload(task) for task in sorted(self._tasks.values(), key=lambda item: item.created_at, reverse=True)]

    def dashboard(self) -> dict[str, Any]:
        tasks = self.list()
        readiness = self.router.registry.readiness()
        return {
            "runtime": "agent_runtime_2.0",
            "task_count": len(tasks),
            "queued": sum(1 for task in tasks if task["status"] == "queued"),
            "awaiting_confirmation": sum(1 for task in tasks if task["status"] == "awaiting_confirmation"),
            "running": sum(1 for task in tasks if task["status"] == "running"),
            "completed": sum(1 for task in tasks if task["status"] == "completed"),
            "failed": sum(1 for task in tasks if task["status"] == "failed"),
            "event_bus": "active",
            "task_queue": "active",
            "shared_context": "local_persistent",
            "agent_readiness": readiness,
            "brain": {
                "skills": BRAIN.catalog(),
                "capacity": BRAIN.capacity_snapshot(),
            },
            "events": self.events.list(limit=20),
        }

    def _require(self, task_id: str) -> RuntimeTask:
        with self._lock:
            try:
                return self._tasks[task_id]
            except KeyError as exc:
                raise ValueError(f"unknown task: {task_id}") from exc

    def _publish(self, task: RuntimeTask, event_type: str, **payload: Any) -> AgentEvent:
        return self.events.publish(
            event_type,
            task.task_id,
            task.selected_agent,
            correlation_id=task.correlation_id,
            run_id=task.run_id,
            **payload,
        )

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None or value == "":
            return None
        return int(value)

    @staticmethod
    def _text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _task_payload(task: RuntimeTask) -> dict[str, Any]:
        return asdict(task)


# Register a fresh, isolated V2 completion crew before the shared runtime starts.
register_completion_crew(ROUTER.registry)
RUNTIME = AgentTaskQueue()
