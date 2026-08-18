import time
import unittest
from threading import Event

from v3.worker_pool import BoundedWorkerPool, WorkerPoolClosedError


class WorkerPoolShutdownTests(unittest.TestCase):
    def test_graceful_shutdown_waits_for_running_work(self):
        pool = BoundedWorkerPool(max_workers=1, max_queue=1)
        started = Event()
        release = Event()

        def blocking(value):
            started.set()
            release.wait(timeout=2)
            return value

        future = pool.submit("task", blocking)
        self.assertTrue(started.wait(timeout=1))
        pool.shutdown(wait=False)
        self.assertTrue(pool.stats().closed)
        with self.assertRaises(WorkerPoolClosedError):
            pool.submit("new", lambda value: value)
        release.set()
        self.assertEqual("task", future.result(timeout=2))
        pool.shutdown(wait=True)
        self.assertEqual(0, pool.stats().active)
        self.assertEqual(0, pool.stats().queued)

    def test_cancel_pending_work_releases_capacity(self):
        pool = BoundedWorkerPool(max_workers=1, max_queue=2)
        started = Event()
        release = Event()

        def blocking(value):
            started.set()
            release.wait(timeout=2)
            return value

        running = pool.submit("running", blocking)
        self.assertTrue(started.wait(timeout=1))
        pending = pool.submit("pending", lambda value: value)
        pool.shutdown(wait=False, cancel_pending=True)
        release.set()
        self.assertEqual("running", running.result(timeout=2))
        deadline = time.time() + 1
        while not pending.cancelled() and time.time() < deadline:
            time.sleep(0.01)
        self.assertTrue(pending.cancelled())
        pool.shutdown(wait=True)
        deadline = time.time() + 1
        while pool.stats().active and time.time() < deadline:
            time.sleep(0.01)
        self.assertEqual(0, pool.stats().active)
        self.assertEqual(0, pool.stats().queued)


if __name__ == "__main__":
    unittest.main()
