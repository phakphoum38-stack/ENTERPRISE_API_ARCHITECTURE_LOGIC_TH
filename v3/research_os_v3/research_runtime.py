from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .research_planner import ResearchPlan, ResearchTask
from .research_queue import DurableResearchQueue, QueueItem, QueueState

TaskHandler = Callable[[ResearchTask], Mapping[str, object] | None]


@dataclass(frozen=True)
class ResearchRunResult:
    run_id: str
    completed: tuple[str, ...]
    failed: tuple[str, ...]
    retried: tuple[str, ...]


class ResearchRuntime:
    """Runs a ResearchPlan through the durable queue without owning providers."""

    def __init__(self, queue: DurableResearchQueue) -> None:
        self.queue = queue

    def enqueue_plan(self, plan: ResearchPlan) -> None:
        for task in plan.tasks:
            self.queue.enqueue(
                task_id=task.task_id,
                payload={
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "dependencies": list(task.dependencies),
                    "priority": task.priority,
                },
                max_attempts=task.max_attempts,
            )

    def run_once(
        self,
        *,
        run_id: str,
        plan: ResearchPlan,
        handlers: Mapping[str, TaskHandler],
    ) -> ResearchRunResult:
        task_map = {task.task_id: task for task in plan.tasks}
        completed: list[str] = []
        failed: list[str] = []
        retried: list[str] = []

        while True:
            item = self.queue.claim_ready()
            if item is None:
                break
            task = task_map[item.task_id]
            handler = handlers.get(task.task_id)
            if handler is None:
                self.queue.fail(item.item_id, error="MissingTaskHandler")
                failed.append(task.task_id)
                continue
            try:
                handler(task)
            except Exception as exc:
                state = self.queue.fail(item.item_id, error=type(exc).__name__)
                if state == QueueState.RETRY:
                    retried.append(task.task_id)
                else:
                    failed.append(task.task_id)
            else:
                self.queue.ack(item.item_id)
                completed.append(task.task_id)

        return ResearchRunResult(
            run_id=run_id,
            completed=tuple(completed),
            failed=tuple(failed),
            retried=tuple(retried),
        )
