from concurrent.futures import ThreadPoolExecutor

from reference.assignment import AssignmentConflict, ReferenceAssignmentService
from reference.runner_registry import RunnerRegistry
from reference.scheduler import ScheduleRequest


def test_two_runners_contending_for_same_job_produce_one_assignment():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})
    registry.register("runner-b", {"python"})
    service = ReferenceAssignmentService(registry)

    def attempt():
        try:
            return ("assigned", service.assign(ScheduleRequest("job-1", "python")))
        except AssignmentConflict:
            return ("conflict", None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))

    assignments = [assignment for status, assignment in results if status == "assigned"]
    conflicts = [result for result in results if result[0] == "conflict"]

    assert len(assignments) == 1
    assert len(conflicts) == 1
    assert service.assignments.get("job-1") == assignments[0]


def test_draining_one_runner_allows_other_runner_to_receive_new_job():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})
    registry.register("runner-b", {"python"})
    registry.set_draining("runner-a")
    service = ReferenceAssignmentService(registry)

    assignment = service.assign(ScheduleRequest("job-2", "python"))

    assert assignment.runner_id == "runner-b"
