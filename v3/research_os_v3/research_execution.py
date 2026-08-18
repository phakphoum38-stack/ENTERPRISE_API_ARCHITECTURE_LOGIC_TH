from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib

from .queue import DurableTaskQueue, QueueTask
from .research_planner import ResearchPlan, ResearchTask, ready_tasks
from .runner import StatelessResearchRunner

TaskHandler = Callable[[ResearchTask, QueueTask], None]


@dataclass(frozen=True)
class ResearchExecutionResult:
    research_id: str
    completed: tuple[str, ...]
    failed: tuple[str, ...]
    retried: tuple[str, ...]


class ResearchExecutionCoordinator:
    """Binds the Research DAG to the existing durable queue/runner boundary."""

    def __init__(self, queue: DurableTaskQueue, *, max_attempts: int = 3) -> None:
        self.queue = queue
        self.runner = StatelessResearchRunner(queue, max_attempts=max_attempts)

    def enqueue_ready(self, plan: ResearchPlan, completed: set[str] | None = None) -> set[str]:
        completed = set(completed or ())
        enqueued: set[str] = set()
        for task in ready_tasks(plan, completed):
            self._enqueue(plan, task)
            enqueued.add(task.id)
        return enqueued

    def _enqueue(self, plan: ResearchPlan, task: ResearchTask) -> None:
        self.queue.enqueue(
            QueueTask(
                task_id=task.id,
                research_id=self.research_id(plan),
                payload={
                    "title": task.title,
                    "question": task.question,
                    "kind": task.kind.value,
                    "depends_on": list(task.depends_on),
                    "priority": task.priority,
                    "metadata": dict(task.metadata),
                },
            )
        )

    @staticmethod
    def research_id(plan: ResearchPlan) -> str:
        return "research-" + hashlib.sha256(plan.question.encode("utf-8")).hexdigest()[:20]

    def run(
        self,
        plan: ResearchPlan,
        handlers: Mapping[str, TaskHandler],
    ) -> ResearchExecutionResult:
        task_map = {task.id: task for task in plan.tasks}
        completed: set[str] = set()
        completed_order: list[str] = []
        failed: list[str] = []
        retried: list[str] = []
        enqueued = self.enqueue_ready(plan)

        def dispatch(item: QueueTask) -> None:
            task = task_map[item.task_id]
            handler = handlers.get(task.id)
            if handler is None:
                raise LookupError(f"missing research handler: {task.id}")
            handler(task, item)

        while True:
            result = self.runner.run_once(dispatch)
            if result is None:
                break
            if result.status == "retry":
                retried.append(result.task_id)
                continue
            if result.status == "failed":
                failed.append(result.task_id)
                continue
            completed.add(result.task_id)
            completed_order.append(result.task_id)
            for task in ready_tasks(plan, completed):
                if task.id not in enqueued:
                    self._enqueue(plan, task)
                    enqueued.add(task.id)

        return ResearchExecutionResult(
            research_id=self.research_id(plan),
            completed=tuple(completed_order),
            failed=tuple(failed),
            retried=tuple(retried),
        )
