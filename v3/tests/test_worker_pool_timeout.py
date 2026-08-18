import time
import unittest

from v3.worker_pool import BoundedWorkerPool, TaskTimeoutError


class WorkerPoolTimeoutTests(unittest.TestCase):
    def test_task_timeout_is_observable(self):
        pool = BoundedWorkerPool(max_workers=1, max_queue=1)

        def slow(_):
            time.sleep(0.2)
            return "done"

        with self.assertRaises(TaskTimeoutError):
            pool.run_with_timeout("slow", slow, timeout=0.02)

        self.assertEqual(1, pool.stats().timed_out)
        pool.shutdown(wait=True)

    def test_invalid_timeout_is_rejected(self):
        pool = BoundedWorkerPool(max_workers=1, max_queue=1)
        with self.assertRaises(ValueError):
            pool.run_with_timeout("task", lambda value: value, timeout=0)
        pool.shutdown()


if __name__ == "__main__":
    unittest.main()
