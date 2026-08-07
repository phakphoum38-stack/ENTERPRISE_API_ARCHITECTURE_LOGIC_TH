from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from agent_platform import AgentRouter


@dataclass
class AgentEvent:
    event_id: str
    event_type: str
    task_id: str
    agent_id: str | None
    timestamp: float
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
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class AgentEventBus:
    def __init__(self, max_events: int = 500) -> None:
        self._max_events = max_events
        self._events: list[AgentEvent] = []
        self._lock = threading.RLock()

    def publish(self, event_type: str, task_id: str, agent_id: str | None = None, **payload: Any) -> AgentEvent:
        event = AgentEvent(str(uuid.uuid4()), event_type, task_id, agent_id, time.time(), payload)
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
        self.router = router or AgentRouter()
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
        task = RuntimeTask(
            task_id=str(uuid.uuid4()),
            objective=objective,
            requested_agent=requested_agent,
            context=dict(context or {}),
            status="queued",
            selected_agent=str(agent["agent_id"]),
            route_reason=str(route["reason"]),
            requires_confirmation=bool(route["requires_confirmation_for_writes"]),
            confirmed=confirmed,
        )
        with self._lock:
            self._tasks[task.task_id] = task
        self.events.publish("task.queued", task.task_id, task.selected_agent, objective=objective)
        return self.execute(task.task_id)

    def confirm(self, task_id: str) -> dict[str, Any]:
        task = self._require(task_id)
        task.confirmed = True
        task.updated_at = time.time()
        self.events.publish("task.confirmed", task.task_id, task.selected_agent)
        return self.execute(task_id)

    def execute(self, task_id: str) -> dict[str, Any]:
        task = self._require(task_id)
        if task.requires_confirmation and not task.confirmed:
            task.status = "awaiting_confirmation"
            task.updated_at = time.time()
            self.events.publish("task.awaiting_confirmation", task.task_id, task.selected_agent)
            return self._task_payload(task)

        task.status = "running"
        task.updated_at = time.time()
        self.events.publish("task.started", task.task_id, task.selected_agent)
        try:
            shared = self.context_store.get(f"shared:{task.selected_agent}")
            merged_context = {**shared, **task.context}
            task.result = {
                "agent_id": task.selected_agent,
                "objective": task.objective,
                "context": merged_context,
                "execution": "runtime_ready",
                "note": "Agent Runtime 1.0 dispatch is active. Domain-specific executors will replace this generic executor incrementally.",
            }
            task.status = "completed"
            task.updated_at = time.time()
            self.context_store.merge(f"shared:{task.selected_agent}", {"last_task_id": task.task_id, "last_objective": task.objective})
            self.events.publish("task.completed", task.task_id, task.selected_agent)
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            task.updated_at = time.time()
            self.events.publish("task.failed", task.task_id, task.selected_agent, error=str(exc))
        return self._task_payload(task)

    def get(self, task_id: str) -> dict[str, Any]:
        return self._task_payload(self._require(task_id))

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._task_payload(task) for task in sorted(self._tasks.values(), key=lambda item: item.created_at, reverse=True)]

    def dashboard(self) -> dict[str, Any]:
        tasks = self.list()
        return {
            "runtime": "agent_runtime_1.0",
            "task_count": len(tasks),
            "queued": sum(1 for task in tasks if task["status"] == "queued"),
            "awaiting_confirmation": sum(1 for task in tasks if task["status"] == "awaiting_confirmation"),
            "running": sum(1 for task in tasks if task["status"] == "running"),
            "completed": sum(1 for task in tasks if task["status"] == "completed"),
            "failed": sum(1 for task in tasks if task["status"] == "failed"),
            "event_bus": "active",
            "task_queue": "active",
            "shared_context": "local_persistent",
            "events": self.events.list(limit=20),
        }

    def _require(self, task_id: str) -> RuntimeTask:
        with self._lock:
            try:
                return self._tasks[task_id]
            except KeyError as exc:
                raise ValueError(f"unknown task: {task_id}") from exc

    @staticmethod
    def _task_payload(task: RuntimeTask) -> dict[str, Any]:
        return asdict(task)


RUNTIME = AgentTaskQueue()
