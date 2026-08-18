from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
from uuid import uuid4


class TaskKind(str, Enum):
    DISCOVER = "discover"
    VERIFY = "verify"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"


@dataclass(frozen=True)
class ResearchTask:
    id: str
    title: str
    question: str
    kind: TaskKind
    depends_on: tuple[str, ...] = ()
    priority: int = 50
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    objective: str
    tasks: tuple[ResearchTask, ...]
    assumptions: tuple[str, ...] = ()

    def task_ids(self) -> tuple[str, ...]:
        return tuple(task.id for task in self.tasks)


class ResearchPlanError(ValueError):
    pass


class ResearchPlanner:
    """Build a deterministic, dependency-safe research DAG.

    This layer intentionally does not call providers. The orchestrator owns
    execution; the planner only turns a research question into executable
    intent.
    """

    def plan(
        self,
        question: str,
        *,
        objective: str | None = None,
        sub_questions: Iterable[str] = (),
        assumptions: Iterable[str] = (),
    ) -> ResearchPlan:
        question = question.strip()
        if not question:
            raise ResearchPlanError("research question must not be empty")

        children = [q.strip() for q in sub_questions if q.strip()]
        if not children:
            children = [question]

        discover_id = self._id("discover")
        discover = ResearchTask(
            id=discover_id,
            title="Discover evidence",
            question=question,
            kind=TaskKind.DISCOVER,
            priority=10,
        )

        tasks: list[ResearchTask] = [discover]
        verify_ids: list[str] = []
        for index, child in enumerate(children, start=1):
            task_id = self._id(f"verify-{index}")
            verify_ids.append(task_id)
            tasks.append(
                ResearchTask(
                    id=task_id,
                    title=f"Verify sub-question {index}",
                    question=child,
                    kind=TaskKind.VERIFY,
                    depends_on=(discover_id,),
                    priority=20,
                )
            )

        analyze_id = self._id("analyze")
        tasks.append(
            ResearchTask(
                id=analyze_id,
                title="Analyze findings",
                question=question,
                kind=TaskKind.ANALYZE,
                depends_on=tuple(verify_ids),
                priority=30,
            )
        )

        synthesis_id = self._id("synthesize")
        tasks.append(
            ResearchTask(
                id=synthesis_id,
                title="Synthesize research",
                question=question,
                kind=TaskKind.SYNTHESIZE,
                depends_on=(analyze_id,),
                priority=40,
            )
        )

        plan = ResearchPlan(
            question=question,
            objective=(objective or question).strip(),
            tasks=tuple(tasks),
            assumptions=tuple(a.strip() for a in assumptions if a.strip()),
        )
        validate_plan(plan)
        return plan

    @staticmethod
    def _id(prefix: str) -> str:
        return f"research-{prefix}-{uuid4().hex[:12]}"


def validate_plan(plan: ResearchPlan) -> None:
    ids = set(plan.task_ids())
    if len(ids) != len(plan.tasks):
        raise ResearchPlanError("task ids must be unique")
    for task in plan.tasks:
        if task.id in task.depends_on:
            raise ResearchPlanError(f"task {task.id} depends on itself")
        missing = set(task.depends_on) - ids
        if missing:
            raise ResearchPlanError(
                f"task {task.id} has missing dependencies: {sorted(missing)}"
            )

    visiting: set[str] = set()
    visited: set[str] = set()
    by_id = {task.id: task for task in plan.tasks}

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise ResearchPlanError("research plan contains a dependency cycle")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in by_id[task_id].depends_on:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task in plan.tasks:
        visit(task.id)


def ready_tasks(plan: ResearchPlan, completed: set[str]) -> tuple[ResearchTask, ...]:
    validate_plan(plan)
    ready = [
        task
        for task in plan.tasks
        if task.id not in completed and set(task.depends_on).issubset(completed)
    ]
    return tuple(sorted(ready, key=lambda task: (task.priority, task.id)))
