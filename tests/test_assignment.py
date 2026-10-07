import pytest

from reference.assignment import AssignmentConflict, ReferenceAssignmentService
from reference.runner_registry import RunnerRegistry
from reference.scheduler import ScheduleRequest, NoRunnerAvailable


def test_assignment_is_idempotent_for_same_job_and_runner():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})
    service = ReferenceAssignmentService(registry)

    first = service.assign(ScheduleRequest("job-1", "python"))
    second = service.assign(ScheduleRequest("job-1", "python"))

    assert first == second


def test_job_cannot_be_reserved_by_two_runners():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})
    registry.register("runner-b", {"python"})
    service = ReferenceAssignmentService(registry)

    first = service.assign(ScheduleRequest("job-1", "python"))
    # Force the selection path to another runner by making the first drain.
    registry.set_draining(first.runner_id)

    with pytest.raises(AssignmentConflict):
        service.assign(ScheduleRequest("job-1", "python"))


def test_draining_runner_is_not_assigned():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})
    registry.set_draining("runner-a")
    service = ReferenceAssignmentService(registry)

    with pytest.raises(NoRunnerAvailable):
        service.assign(ScheduleRequest("job-1", "python"))
