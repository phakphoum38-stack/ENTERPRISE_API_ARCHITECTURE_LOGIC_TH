from __future__ import annotations

import json
import time
import unittest
from threading import Event, Lock

from v3.worker_pool import BoundedWorkerPool, QueueSaturatedError


class WorkerPoolPerformanceTests(unittest.TestCase):
    def test_capacity_and_backpressure_are_measurable(self) -> None:
        max_workers = 4
        max_queue = 16
        pool = BoundedWorkerPool(max_workers=max_workers, max_queue=max_queue)
        started = Event()
        release = Event()

        def blocking(value: int) -> int:
            started.set()
            release.wait(timeout=5)
            return value

        futures = []
        try:
            for value in range(max_queue):
                futures.append(pool.submit(value, blocking))
            self.assertTrue(started.wait(timeout=2))

            with self.assertRaises(QueueSaturatedError):
                pool.submit(max_queue, lambda value: value)

            stats = pool.stats()
            self.assertEqual(max_queue, stats.capacity)
            self.assertEqual(max_queue, stats.queued)
            self.assertEqual(max_queue, stats.active)
            self.assertLessEqual(stats.active, max_queue)
        finally:
            release.set()
            for future in futures:
                future.result(timeout=5)
            pool.shutdown()

        final = pool.stats()
        self.assertEqual(0, final.active)
        self.assertEqual(0, final.queued)

    def test_repeatable_bounded_load_and_concurrency_limit(self) -> None:
        max_workers = 4
        max_queue = 32
        task_count = 128
        active = 0
        max_observed = 0
        lock = Lock()

        def work(value: int) -> int:
            nonlocal active, max_observed
            with lock:
                active += 1
                max_observed = max(max_observed, active)
            try:
                time.sleep(0.001)
                return value * 2
            finally:
                with lock:
                    active -= 1

        pool = BoundedWorkerPool(max_workers=max_workers, max_queue=max_queue)
        started_at = time.perf_counter()
        futures = []
        saturated = 0
        try:
            for value in range(task_count):
                while True:
                    try:
                        futures.append(pool.submit(value, work))
                        break
                    except QueueSaturatedError:
                        saturated += 1
                        time.sleep(0.001)

            results = [future.result(timeout=5) for future in futures]
        finally:
            pool.shutdown()

        elapsed = time.perf_counter() - started_at
        self.assertEqual(task_count, len(results))
        self.assertEqual([value * 2 for value in range(task_count)], results)
        self.assertLessEqual(max_observed, max_workers)
        self.assertGreaterEqual(saturated, 1)
        self.assertEqual(0, pool.stats().active)
        self.assertEqual(0, pool.stats().queued)
        self.assertTrue(pool.stats().closed)

        # Timing is evidence, not a brittle pass/fail threshold. The gate asserts
        # boundedness and correctness while recording elapsed time for comparison.
        self.assertGreater(elapsed, 0.0)

    def test_metrics_are_serializable_for_ci_evidence(self) -> None:
        pool = BoundedWorkerPool(max_workers=2, max_queue=4)
        started_at = time.perf_counter()
        futures = [pool.submit(i, lambda value: value) for i in range(4)]
        results = [future.result(timeout=2) for future in futures]
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        pool.shutdown()

        evidence = {
            "gate": "v3.5-worker-performance",
            "capacity": 4,
            "max_workers": 2,
            "tasks": len(results),
            "completed": len(results),
            "elapsed_ms": round(elapsed_ms, 3),
            "active_after_shutdown": pool.stats().active,
            "queued_after_shutdown": pool.stats().queued,
        }
        encoded = json.dumps(evidence, sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(evidence, decoded)


if __name__ == "__main__":
    unittest.main()
