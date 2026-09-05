from reference.execution_loop import ReferenceExecutionLoop
from reference.jobstore import InMemoryJobStore
from reference.queue import InMemoryQueueAdapter
from reference.runner import RunnerConfig, StatelessRunner


def test_runner_executes_queued_job_without_local_job_state():
    loop = ReferenceExecutionLoop(InMemoryJobStore(), InMemoryQueueAdapter())
    job = loop.submit("wf-1", "idem-1", {"value": 42})
    runner = StatelessRunner(loop, RunnerConfig("runner-a", max_jobs_per_cycle=2))
    seen = []

    results = runner.run_until_empty(lambda payload: seen.append(payload["value"]))

    assert [result.job_id for result in results] == [job.job_id]
    assert results[0].status == "SUCCEEDED"
    assert seen == [42]
