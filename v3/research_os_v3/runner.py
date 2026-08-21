from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .queue import DurableTaskQueue, QueueTask


TaskHandler = Callable[[QueueTask], None]
EventSink = Callable[[str, str, dict[str, Any]], None]


@dataclass(frozen=True)
class RunnerResult:
    task_id: str
    status: str
    attempts: int
    error_type: str | None = None


class StatelessResearchRunner:
    """One-shot stateless runner with explicit queue lease ownership."""

    def __init__(
        self,
        queue: DurableTaskQueue,
        *,
        max_attempts: int = 3,
        worker_id: str = "runner",
        event_sink: EventSink | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if not worker_id:
            raise ValueError("worker_id must not be empty")
        self.queue = queue
        self.max_attempts = max_attempts
        self.worker_id = worker_id
        self._event_sink = event_sink

    def run_once(self, handler: TaskHandler) -> RunnerResult | None:
        task = self.queue.claim(worker_id=self.worker_id)
        if task is None:
            self._emit("runner.idle", "__runner__")
            return None
        assert task.lease_id is not None
        self._emit(
            "runner.claimed",
            task.task_id,
            research_id=task.research_id,
            worker_id=self.worker_id,
            attempts=task.attempts,
            lease_id=task.lease_id,
        )
        try:
            handler(task)
        except Exception as exc:
            error_type = type(exc).__name__
            if task.attempts + 1 < self.max_attempts:
                self.queue.retry(task.task_id, task.lease_id)
                self._emit(
                    "runner.retry",
                    task.task_id,
                    worker_id=self.worker_id,
                    attempts=task.attempts + 1,
                    error_type=error_type,
                )
                return RunnerResult(task.task_id, "retry", task.attempts + 1, error_type)
            self.queue.fail(task.task_id, task.lease_id)
            self._emit(
                "runner.failed",
                task.task_id,
                worker_id=self.worker_id,
                attempts=task.attempts + 1,
                error_type=error_type,
            )
            return RunnerResult(task.task_id, "failed", task.attempts + 1, error_type)
        self.queue.ack(task.task_id, task.lease_id)
        self._emit(
            "runner.completed",
            task.task_id,
            research_id=task.research_id,
            worker_id=self.worker_id,
            attempts=task.attempts,
        )
        return RunnerResult(task.task_id, "completed", task.attempts)

    def _emit(self, event_type: str, task_id: str, **detail: Any) -> None:
        if self._event_sink is None:
            return
        try:
            self._event_sink(event_type, task_id, detail)
        except Exception:
            # Telemetry is fail-safe and must never alter execution semantics.
            return
