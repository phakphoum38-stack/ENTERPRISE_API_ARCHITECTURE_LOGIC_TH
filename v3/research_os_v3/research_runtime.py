from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .research_planner import ResearchPlan, ResearchTask, ready_tasks
from .research_queue import DurableResearchQueue, QueueState

TaskHandler = Callable[[ResearchTask], Mapping[str, object] | None]


@dataclass(frozen=True)
class ResearchRunResult:
    run_id: str
    completed: tuple[str, ...]
    failed: tuple[str, ...]
    retried: tuple[str, ...]


class ResearchRuntime:
    """Runs a ResearchPlan through a durable queue without owning providers."""

    def __init__(self, queue: DurableResearchQueue) -> None:
        self.queue = queue

    def enqueue_plan(self, plan: ResearchPlan) -> None:
        for task in ready_tasks(plan, set()):
            self._enqueue(task)

    def _enqueue(self, task: ResearchTask) -> None:
        self.queue.enqueue(
            task_id=task.id,
            payload={
                "task_id": task.id,
                "title": task.title,
                "question": task.question,
                "kind": task.kind.value,
                "dependencies": list(task.depends_on),
                "priority": task.priority,
            },
            max_attempts=3,
        )

    def run_once(
        self,
        *,
        run_id: str,
        plan: ResearchPlan,
        handlers: Mapping[str, TaskHandler],
    ) -> ResearchRunResult:
        task_map = {task.id: task for task in plan.tasks}
        completed: set[str] = set()
        completed_order: list[str] = []
        failed: list[str] = []
        retried: list[str] = []
        enqueued: set[str] = {task.id for task in ready_tasks(plan, set())}

        while True:
            item = self.queue.claim_ready()
            if item is None:
                break
            task = task_map[item.task_id]
            handler = handlers.get(task.id)
            if handler is None:
                state = self.queue.fail(item.item_id, error="MissingTaskHandler")
                if state == QueueState.RETRY:
                    retried.append(task.id)
                else:
                    failed.append(task.id)
                continue
            try:
                handler(task)
            except Exception as exc:
                state = self.queue.fail(item.item_id, error=type(exc).__name__)
                if state == QueueState.RETRY:
                    retried.append(task.id)
                else:
                    failed.append(task.id)
            else:
                self.queue.ack(item.item_id)
                completed.add(task.id)
                completed_order.append(task.id)
                for next_task in ready_tasks(plan, completed):
                    if next_task.id not in enqueued:
                        self._enqueue(next_task)
                        enqueued.add(next_task.id)

        return ResearchRunResult(
            run_id=run_id,
            completed=tuple(completed_order),
            failed=tuple(failed),
            retried=tuple(retried),
        )
