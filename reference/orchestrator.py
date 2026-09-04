from dataclasses import dataclass
from typing import Any, Callable

from reference.assignment import Assignment, ReferenceAssignmentService
from reference.execution_loop import ReferenceExecutionLoop, ExecutionResult
from reference.scheduler import ScheduleRequest
from reference.queue import InMemoryQueueAdapter


@dataclass(frozen=True)
class DispatchResult:
    job_id: str
    assignment: Assignment


class ReferenceOrchestrator:
    """Reference Queue -> Scheduler -> Assignment -> Runner orchestration boundary."""

    def __init__(self, execution_loop: ReferenceExecutionLoop, assignment: ReferenceAssignmentService) -> None:
        self.execution_loop = execution_loop
        self.assignment = assignment

    def dispatch_once(self, capability: str | None = None) -> DispatchResult:
        message = self.execution_loop.queue.receive()
        assignment = self.assignment.assign(ScheduleRequest(message.job_id, capability))
        # The assignment is the durable-facing scheduling decision; execution is still
        # performed through the existing lease-aware execution loop.
        self.execution_loop.queue.reject(message, requeue=True)
        return DispatchResult(message.job_id, assignment)

    def execute_assigned(self, runner_id: str, handler: Callable[[dict[str, Any]], Any]) -> ExecutionResult:
        return self.execution_loop.process_once(runner_id, handler)
