import threading
import time

import pytest

from reference.jobstore import InMemoryJobStore, LeaseConflict


def test_idempotent_create():
    store = InMemoryJobStore()
    a = store.create("wf-1", "idem-1", {"x": 1})
    b = store.create("wf-1", "idem-1", {"x": 2})
    assert a.job_id == b.job_id


def test_only_one_runner_can_claim():
    store = InMemoryJobStore()
    job = store.create("wf-1", "idem-1", {})
    winners = []
    lock = threading.Lock()

    def claim(runner):
        try:
            claimed = store.claim(job.job_id, runner, lease_seconds=10)
            with lock:
                winners.append(claimed.lease_owner)
        except LeaseConflict:
            pass

    threads = [threading.Thread(target=claim, args=(f"runner-{i}",)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(winners) == 1


def test_stale_lease_cannot_complete_reclaimed_job():
    store = InMemoryJobStore()
    job = store.create("wf-1", "idem-1", {})
    first = store.claim(job.job_id, "runner-a", lease_seconds=0)
    time.sleep(0.01)
    second = store.claim(job.job_id, "runner-b", lease_seconds=10)

    assert second.lease_id != first.lease_id
    with pytest.raises(LeaseConflict):
        store.complete(job.job_id, first.lease_id)


def test_retry_then_dead_letter():
    store = InMemoryJobStore()
    job = store.create("wf-1", "idem-1", {}, max_attempts=2)
    lease = store.claim(job.job_id, "runner-a")
    assert store.fail(job.job_id, lease.lease_id).status == "RETRYING"
    lease = store.claim(job.job_id, "runner-a")
    assert store.fail(job.job_id, lease.lease_id).status == "DEAD_LETTER"
