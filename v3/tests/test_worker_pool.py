import time
import unittest
from threading import Event

from v3.worker_pool import BoundedWorkerPool, QueueSaturatedError


class WorkerPoolTests(unittest.TestCase):
    def test_queue_is_bounded_and_applies_backpressure(self):
        pool = BoundedWorkerPool(max_workers=1, max_queue=1)
        started = Event()
        release = Event()

        def blocking(value):
            started.set()
            release.wait(timeout=2)
            return value

        first = pool.submit("first", blocking)
        self.assertTrue(started.wait(timeout=1))
        second = pool.submit("second", lambda value: value)
        with self.assertRaises(QueueSaturatedError):
            pool.submit("third", lambda value: value)

        release.set()
        self.assertEqual("first", first.result(timeout=2))
        self.assertEqual("second", second.result(timeout=2))
        pool.shutdown()

    def test_active_count_returns_to_zero(self):
        pool = BoundedWorkerPool(max_workers=2, max_queue=2)
        future = pool.submit("task", lambda value: value)
        self.assertEqual("task", future.result(timeout=2))
        deadline = time.time() + 1
        while pool.stats().active and time.time() < deadline:
            time.sleep(0.01)
        self.assertEqual(0, pool.stats().active)
        self.assertEqual(0, pool.stats().queued)
        pool.shutdown()

    def test_shutdown_rejects_new_work(self):
        pool = BoundedWorkerPool(max_workers=1, max_queue=1)
        pool.shutdown()
        with self.assertRaises(RuntimeError):
            pool.submit("task", lambda value: value)


if __name__ == "__main__":
    unittest.main()
