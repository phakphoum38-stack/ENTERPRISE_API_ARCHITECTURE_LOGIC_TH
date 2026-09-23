from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from threading import Lock

from .event_delivery import DurableEventDelivery, EventEnvelope
from .worker_pool import StatelessWorkerPool

class WorkerPoolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.delivery = DurableEventDelivery(Path(self.tmp.name) / "events.db")
        for i in range(4):
            self.delivery.append(EventEnvelope(event_id=f"e{i}", event_type="task", occurred_at="2026-01-01T00:00:00+00:00", workflow_id="w", task_id=f"t{i}", correlation_id="c", causation_id="root", sequence=i, producer="test", payload={"i": i}))
            self.delivery.register_delivery(event_id=f"e{i}", consumer="runner", delivery_id=f"d{i}", idempotency_key=f"k{i}")
    def tearDown(self) -> None:
        self.tmp.cleanup()
    def test_concurrency_never_exceeds_limit(self) -> None:
        lock, active, peak = Lock(), 0, 0
        def handler(_delivery):
            nonlocal active, peak
            with lock:
                active += 1; peak = max(peak, active)
            time.sleep(0.03)
            with lock: active -= 1
        results = StatelessWorkerPool(self.delivery, concurrency=2, handler=handler).run_once([f"d{i}" for i in range(4)])
        self.assertEqual(sum(r.status == "acked" for r in results), 4)
        self.assertLessEqual(peak, 2)
    def test_failed_handler_is_not_acked(self) -> None:
        results = StatelessWorkerPool(self.delivery, concurrency=1, handler=lambda _: (_ for _ in ()).throw(RuntimeError("boom"))).run_once(["d0"])
        self.assertEqual(results[0].status, "failed")
        self.assertEqual(self.delivery.get_delivery("d0").status, "delivering")
    def test_duplicate_ack_is_harmless(self) -> None:
        seen = []
        result = StatelessWorkerPool(self.delivery, concurrency=1, handler=lambda d: seen.append(d.event_id)).run_once(["d0"])
        self.assertEqual(result[0].status, "acked")
        self.assertEqual(seen, ["e0"])
        self.assertEqual(self.delivery.get_delivery("d0").status, "acked")

if __name__ == "__main__": unittest.main()
