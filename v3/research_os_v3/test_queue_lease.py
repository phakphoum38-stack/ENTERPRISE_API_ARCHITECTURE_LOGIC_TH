from __future__ import annotations

import time

import pytest

from .queue import DurableTaskQueue, LeaseOwnershipError, QueueTask


def make_queue(tmp_path):
    return DurableTaskQueue(tmp_path / "queue.db", default_lease_seconds=1)


def enqueue(queue: DurableTaskQueue, task_id: str = "task-1") -> None:
    queue.enqueue(QueueTask(task_id=task_id, research_id="research-1", payload={"x": 1}))


def test_claim_assigns_unique_lease_and_worker(tmp_path):
    queue = make_queue(tmp_path)
    enqueue(queue)

    task = queue.claim(worker_id="worker-a")

    assert task is not None
    assert task.lease_id
    assert task.lease_until


def test_wrong_owner_cannot_ack(tmp_path):
    queue = make_queue(tmp_path)
    enqueue(queue)
    task = queue.claim(worker_id="worker-a")
    assert task is not None and task.lease_id

    with pytest.raises(LeaseOwnershipError):
        queue.ack(task.task_id, "wrong-lease")


def test_renew_extends_active_lease(tmp_path):
    queue = make_queue(tmp_path)
    enqueue(queue)
    task = queue.claim(worker_id="worker-a")
    assert task is not None and task.lease_id
    original_until = task.lease_until

    renewed = queue.renew_lease(task.task_id, task.lease_id, lease_seconds=2)

    assert renewed.lease_until != original_until


def test_expired_lease_is_recoverable(tmp_path):
    queue = make_queue(tmp_path)
    enqueue(queue)
    task = queue.claim(worker_id="worker-a")
    assert task is not None

    time.sleep(1.1)
    assert queue.recover_expired_leases() == 1

    recovered = queue.claim(worker_id="worker-b")
    assert recovered is not None
    assert recovered.lease_id != task.lease_id


def test_expired_lease_cannot_ack(tmp_path):
    queue = make_queue(tmp_path)
    enqueue(queue)
    task = queue.claim(worker_id="worker-a")
    assert task is not None and task.lease_id

    time.sleep(1.1)
    with pytest.raises(LeaseOwnershipError):
        queue.ack(task.task_id, task.lease_id)
