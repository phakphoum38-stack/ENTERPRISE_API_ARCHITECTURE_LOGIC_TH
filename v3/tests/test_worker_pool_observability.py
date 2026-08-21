import unittest
from threading import Event

from v3.worker_pool import BoundedWorkerPool, QueueSaturatedError, TaskTimeoutError


class WorkerPoolObservabilityTests(unittest.TestCase):
    def test_lifecycle_events_are_emitted(self):
        events = []

        def sink(event_type, task_id, detail):
            events.append((event_type, task_id, detail))

        pool = BoundedWorkerPool(max_workers=1, max_queue=1, event_sink=sink)
        future = pool.submit("task-1", lambda value: value)
        self.assertEqual("task-1", future.result(timeout=2))
        pool.shutdown()

        names = [item[0] for item in events]
        self.assertIn("worker.submitted", names)
        self.assertIn("worker.started", names)
        self.assertIn("worker.completed", names)
        self.assertIn("worker.shutdown", names)

    def test_saturation_and_timeout_events_are_emitted(self):
        events = []
        started = Event()
        release = Event()

        def sink(event_type, task_id, detail):
            events.append((event_type, task_id, detail))

        def blocking(value):
            started.set()
            release.wait(timeout=2)
            return value

        pool = BoundedWorkerPool(max_workers=1, max_queue=1, event_sink=sink)
        future = pool.submit("blocking", blocking)
        self.assertTrue(started.wait(timeout=1))
        with self.assertRaises(QueueSaturatedError):
            pool.submit("saturated", lambda value: value)

        release.set()
        self.assertEqual("blocking", future.result(timeout=2))

        with self.assertRaises(TaskTimeoutError):
            pool.run_with_timeout("timeout", lambda value: (Event().wait(0.2), value)[1], 0.01)
        pool.shutdown()

        names = [item[0] for item in events]
        self.assertIn("worker.saturated", names)
        self.assertIn("worker.timeout", names)

    def test_observability_sink_failure_does_not_break_pool(self):
        def failing_sink(event_type, task_id, detail):
            raise RuntimeError("telemetry unavailable")

        pool = BoundedWorkerPool(max_workers=1, max_queue=1, event_sink=failing_sink)
        self.assertEqual("ok", pool.submit("ok", lambda value: value).result(timeout=2))
        pool.shutdown()


if __name__ == "__main__":
    unittest.main()
