from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .queue import DurableTaskQueue, QueueTask


TaskHandler = Callable[[QueueTask], None]


@dataclass(frozen=True)
class RunnerResult:
    task_id: str
    status: str
    attempts: int
    error_type: str | None = None


class StatelessResearchRunner:
    """One-shot runner that owns no task state outside the queue."""

    def __init__(self, queue: DurableTaskQueue, *, max_attempts: int = 3) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.queue = queue
        self.max_attempts = max_attempts

    def run_once(self, handler: TaskHandler) -> RunnerResult | None:
        task = self.queue.claim()
        if task is None:
            return None
        try:
            handler(task)
        except Exception as exc:
            if task.attempts + 1 < self.max_attempts:
                self.queue.retry(task.task_id)
                return RunnerResult(task.task_id, "retry", task.attempts + 1, type(exc).__name__)
            self.queue.fail(task.task_id)
            return RunnerResult(task.task_id, "failed", task.attempts + 1, type(exc).__name__)
        self.queue.ack(task.task_id)
        return RunnerResult(task.task_id, "completed", task.attempts)
