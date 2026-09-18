from __future__ import annotations

import threading
import time

import pytest

from v3.worker_pool import BoundedWorkerPool, WorkerPoolClosedError, WorkerPoolLifecycle


def test_drain_closes_admission_and_waits_for_active_work() -> None:
    started = threading.Event()
    release = threading.Event()

    def work(_: str) -> str:
        started.set()
        release.wait(timeout=2)
        return "done"

    pool = BoundedWorkerPool[str, str](max_workers=1, max_queue=2)
    future = pool.submit("task-1", work)
    assert started.wait(timeout=1)

    assert pool.begin_drain() is WorkerPoolLifecycle.DRAINING
    with pytest.raises(WorkerPoolClosedError):
        pool.submit("task-2", work)

    result = []
    waiter = threading.Thread(target=lambda: result.append(pool.wait_for_drain(timeout=2)))
    waiter.start()
    time.sleep(0.05)
    assert pool.stats().lifecycle is WorkerPoolLifecycle.DRAINING

    release.set()
    waiter.join(timeout=2)

    assert result == [True]
    assert future.result(timeout=1) == "done"
    assert pool.stats().lifecycle is WorkerPoolLifecycle.DRAINED
    pool.shutdown()
    assert pool.stats().lifecycle is WorkerPoolLifecycle.SHUTDOWN
