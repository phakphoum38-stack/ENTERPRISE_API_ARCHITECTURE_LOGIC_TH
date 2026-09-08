from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

from reference.runner_registry import RunnerRegistry
from reference.scheduler import ReferenceScheduler, ScheduleRequest, NoRunnerAvailable


class AssignmentConflict(Exception):
    pass


@dataclass(frozen=True)
class Assignment:
    job_id: str
    runner_id: str
    assignment_id: str


class AssignmentStore:
    """Reference atomic reservation store used to fence scheduler races."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._assignments: dict[str, Assignment] = {}

    def reserve(self, job_id: str, runner_id: str) -> Assignment:
        with self._lock:
            existing = self._assignments.get(job_id)
            if existing is not None:
                if existing.runner_id == runner_id:
                    return existing
                raise AssignmentConflict("job is already assigned")
            assignment = Assignment(job_id, runner_id, str(uuid4()))
            self._assignments[job_id] = assignment
            return assignment

    def get(self, job_id: str) -> Assignment | None:
        with self._lock:
            return self._assignments.get(job_id)


class ReferenceAssignmentService:
    def __init__(self, registry: RunnerRegistry) -> None:
        self.scheduler = ReferenceScheduler(registry)
        self.registry = registry
        self.assignments = AssignmentStore()

    def assign(self, request: ScheduleRequest) -> Assignment:
        runner = self.scheduler.select(request)
        # Re-check state immediately before reservation to close the drain race.
        healthy = {r.runner_id for r in self.registry.list_healthy(request.capability)}
        if runner.runner_id not in healthy:
            raise NoRunnerAvailable("runner became unavailable before reservation")
        return self.assignments.reserve(request.job_id, runner.runner_id)
