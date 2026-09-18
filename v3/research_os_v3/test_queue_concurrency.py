from __future__ import annotations

import threading

from .queue import DurableTaskQueue, QueueTask


def test_concurrent_claim_has_exactly_one_winner(tmp_path) -> None:
    queue = DurableTaskQueue(tmp_path / "queue.db", default_lease_seconds=30)
    queue.enqueue(QueueTask("task-1", "research-1", {"x": 1}))

    barrier = threading.Barrier(2)
    results: list[object] = []
    lock = threading.Lock()

    def claim(worker_id: str) -> None:
        barrier.wait(timeout=2)
        task = queue.claim(worker_id=worker_id, lease_seconds=30)
        with lock:
            results.append(task)

    threads = [threading.Thread(target=claim, args=(f"worker-{i}",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)

    winners = [task for task in results if task is not None]
    assert len(winners) == 1
    assert winners[0].task_id == "task-1"
    queue.close()
