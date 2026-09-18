import threading
import time
import unittest

from v3.worker_pool import BoundedWorkerPool, WorkerPoolClosedError, WorkerPoolLifecycle


class WorkerPoolDrainTests(unittest.TestCase):
    def test_drain_closes_admission_and_waits_for_active_work(self):
        started = threading.Event()
        release = threading.Event()

        def work(value):
            started.set()
            release.wait(timeout=2)
            return value

        pool = BoundedWorkerPool(max_workers=1, max_queue=2)
        try:
            future = pool.submit("task-1", work)
            self.assertTrue(started.wait(timeout=1))
            self.assertIs(pool.begin_drain(), WorkerPoolLifecycle.DRAINING)
            with self.assertRaises(WorkerPoolClosedError):
                pool.submit("task-2", work)

            result = []
            waiter = threading.Thread(target=lambda: result.append(pool.wait_for_drain(timeout=2)))
            waiter.start()
            time.sleep(0.05)
            self.assertIs(pool.stats().lifecycle, WorkerPoolLifecycle.DRAINING)

            release.set()
            waiter.join(timeout=2)

            self.assertEqual([True], result)
            self.assertEqual("task-1", future.result(timeout=1))
            self.assertIs(pool.stats().lifecycle, WorkerPoolLifecycle.DRAINED)
        finally:
            pool.shutdown()

if __name__ == "__main__":
    unittest.main()
