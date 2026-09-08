from reference.assignment import ReferenceAssignmentService
from reference.execution_loop import ReferenceExecutionLoop
from reference.jobstore import InMemoryJobStore
from reference.orchestrator import ReferenceOrchestrator
from reference.queue import InMemoryQueueAdapter
from reference.runner_registry import RunnerRegistry


def test_queue_scheduler_assignment_and_runner_execution():
    store = InMemoryJobStore()
    queue = InMemoryQueueAdapter()
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})

    loop = ReferenceExecutionLoop(store, queue)
    assignment = ReferenceAssignmentService(registry)
    orchestrator = ReferenceOrchestrator(loop, assignment)

    job = loop.submit("wf-1", "idem-1", {"value": 9})
    dispatch = orchestrator.dispatch_once("python")

    assert dispatch.job_id == job.job_id
    assert dispatch.assignment.runner_id == "runner-a"

    seen = []
    result = orchestrator.execute_assigned("runner-a", lambda payload: seen.append(payload["value"]))

    assert result.status == "SUCCEEDED"
    assert seen == [9]
