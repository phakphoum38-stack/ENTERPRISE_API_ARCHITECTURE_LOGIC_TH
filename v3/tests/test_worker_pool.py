import threading
import time
import unittest

from research_os_v3.worker_pool import BoundedWorkerPool, WorkerTask


class WorkerPoolTests(unittest.TestCase):
    def test_bounded_concurrency_never_exceeds_limit(self):
        lock = threading.Lock()
        active = 0
        maximum = 0

        def worker(value):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.03)
            with lock:
                active -= 1
            return value * 2

        pool = BoundedWorkerPool(worker, max_workers=3, max_queue=10)
        pool.start()
        for i in range(8):
            pool.submit(WorkerTask(str(i), i))
        results = [pool.get_result(timeout=2) for _ in range(8)]
        pool.shutdown()
        self.assertLessEqual(maximum, 3)
        self.assertEqual(sorted(r.value for r in results), [i * 2 for i in range(8)])

    def test_failure_is_reported_and_ownership_callback_runs(self):
        failures = []

        def worker(_):
            raise RuntimeError("boom")

        def on_failure(task, error):
            failures.append((task.task_id, str(error)))

        pool = BoundedWorkerPool(worker, max_workers=1, max_queue=2, on_failure=on_failure)
        pool.start()
        pool.submit(WorkerTask("crash-1", "payload"))
        result = pool.get_result(timeout=2)
        pool.shutdown()
        self.assertIsInstance(result.error, RuntimeError)
        self.assertEqual(failures, [("crash-1", "boom")])

    def test_lease_renewal_runs_during_long_task(self):
        renewals = []
        started = threading.Event()

        def worker(_):
            started.set()
            time.sleep(0.12)
            return "ok"

        def renew(task):
            renewals.append(task.task_id)

        pool = BoundedWorkerPool(
            worker,
            max_workers=1,
            max_queue=1,
            lease_renew=renew,
            renew_interval=0.02,
        )
        pool.start()
        pool.submit(WorkerTask("lease-1", "payload"))
        self.assertTrue(started.wait(1))
        result = pool.get_result(timeout=2)
        pool.shutdown()
        self.assertEqual(result.value, "ok")
        self.assertGreaterEqual(len(renewals), 2)
        self.assertTrue(all(item == "lease-1" for item in renewals))

    def test_graceful_shutdown_drains_running_tasks(self):
        completed = []

        def worker(value):
            time.sleep(0.03)
            completed.append(value)
            return value

        pool = BoundedWorkerPool(worker, max_workers=2, max_queue=4)
        pool.start()
        for i in range(4):
            pool.submit(WorkerTask(str(i), i))
        pool.shutdown(wait=True, timeout=2)
        self.assertEqual(sorted(completed), [0, 1, 2, 3])


if __name__ == "__main__":
    unittest.main()
