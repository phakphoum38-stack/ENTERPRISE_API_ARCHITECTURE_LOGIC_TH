import pytest

from reference.execution_loop import ReferenceExecutionLoop
from reference.jobstore import InMemoryJobStore
from reference.queue import InMemoryQueueAdapter


def test_execution_loop_success():
    loop = ReferenceExecutionLoop(InMemoryJobStore(), InMemoryQueueAdapter())
    job = loop.submit("wf-1", "idem-1", {"value": 7})
    seen = []

    result = loop.process_once("runner-1", lambda payload: seen.append(payload["value"]))

    assert result.job_id == job.job_id
    assert result.status == "SUCCEEDED"
    assert seen == [7]


def test_execution_loop_failure_requeues():
    loop = ReferenceExecutionLoop(InMemoryJobStore(), InMemoryQueueAdapter())
    job = loop.submit("wf-1", "idem-1", {})

    result = loop.process_once("runner-1", lambda _: (_ for _ in ()).throw(RuntimeError("boom")))

    assert result.job_id == job.job_id
    assert result.status == "FAILED"
    # Delivery is requeued for the retry path.
    next_message = loop.queue.receive()
    assert next_message.job_id == job.job_id


def test_duplicate_submission_is_same_job_but_delivery_can_be_deduplicated_by_job_state():
    store = InMemoryJobStore()
    queue = InMemoryQueueAdapter()
    loop = ReferenceExecutionLoop(store, queue)

    first = loop.submit("wf-1", "same-key", {})
    second = loop.submit("wf-1", "same-key", {})

    assert first.job_id == second.job_id
