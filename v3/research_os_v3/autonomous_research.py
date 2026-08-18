from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .research_checkpoint import ResearchCheckpoint, ResearchCheckpointStore
from .research_planner import ResearchPlan, ResearchTask, ready_tasks

TaskHandler = Callable[[ResearchTask], tuple[str, ...]]


@dataclass(frozen=True)
class AutonomousResearchResult:
    run_id: str
    completed: tuple[str, ...]
    failed: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    status: str


class AutonomousResearchLoop:
    """Deterministic control loop for resumable research.

    Tool/provider execution remains outside this class. A handler executes a
    ready task and returns evidence identifiers. The loop owns progress,
    checkpointing, and deciding what becomes ready next.
    """

    def __init__(self, checkpoints: ResearchCheckpointStore) -> None:
        self.checkpoints = checkpoints

    def run(
        self,
        *,
        run_id: str,
        plan: ResearchPlan,
        handlers: Mapping[str, TaskHandler],
        max_steps: int = 100,
    ) -> AutonomousResearchResult:
        checkpoint = self.checkpoints.load(run_id)
        if checkpoint is None:
            checkpoint = ResearchCheckpoint(
                run_id=run_id,
                plan_question=plan.question,
            )

        completed = set(checkpoint.completed_tasks)
        failed = set(checkpoint.failed_tasks)
        evidence = list(checkpoint.evidence_ids)

        for _ in range(max_steps):
            ready = ready_tasks(plan, completed)
            if not ready:
                status = "completed" if len(completed) == len(plan.tasks) else "blocked"
                self._save(run_id, plan, completed, failed, evidence, status)
                return AutonomousResearchResult(run_id, tuple(sorted(completed)), tuple(sorted(failed)), tuple(evidence), status)

            progressed = False
            for task in ready:
                handler = handlers.get(task.id)
                if handler is None:
                    failed.add(task.id)
                    self._save(run_id, plan, completed, failed, evidence, "failed")
                    continue
                try:
                    evidence.extend(handler(task))
                except Exception:
                    failed.add(task.id)
                    self._save(run_id, plan, completed, failed, evidence, "failed")
                    continue
                completed.add(task.id)
                progressed = True
                self._save(run_id, plan, completed, failed, evidence, "running")

            if not progressed:
                self._save(run_id, plan, completed, failed, evidence, "blocked")
                return AutonomousResearchResult(run_id, tuple(sorted(completed)), tuple(sorted(failed)), tuple(evidence), "blocked")

        self._save(run_id, plan, completed, failed, evidence, "paused")
        return AutonomousResearchResult(run_id, tuple(sorted(completed)), tuple(sorted(failed)), tuple(evidence), "paused")

    def _save(self, run_id: str, plan: ResearchPlan, completed: set[str], failed: set[str], evidence: list[str], status: str) -> None:
        self.checkpoints.save(
            ResearchCheckpoint(
                run_id=run_id,
                plan_question=plan.question,
                completed_tasks=tuple(sorted(completed)),
                failed_tasks=tuple(sorted(failed)),
                evidence_ids=tuple(dict.fromkeys(evidence)),
                metadata={"status": status},
            )
        )
