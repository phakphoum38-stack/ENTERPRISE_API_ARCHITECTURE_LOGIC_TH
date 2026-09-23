from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Callable, Iterable

from .event_delivery import Delivery, DurableEventDelivery

@dataclass(frozen=True)
class WorkerResult:
    delivery_id: str
    worker_id: str
    status: str
    error_type: str | None = None

class StatelessWorkerPool:
    """Bounded stateless workers over the existing durable delivery contract."""
    def __init__(self, delivery: DurableEventDelivery, *, concurrency: int, handler: Callable[[Delivery], None], worker_prefix: str = "runner") -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self.delivery, self.concurrency, self.handler, self.worker_prefix = delivery, concurrency, handler, worker_prefix

    def run_once(self, delivery_ids: Iterable[str]) -> tuple[WorkerResult, ...]:
        ids = tuple(delivery_ids)
        if not ids:
            return ()
        with ThreadPoolExecutor(max_workers=self.concurrency, thread_name_prefix=self.worker_prefix) as pool:
            futures: dict[Future[WorkerResult], str] = {pool.submit(self._execute, d, i): d for i, d in enumerate(ids)}
            done, _ = wait(futures)
            return tuple(f.result() for f in done)

    def _execute(self, delivery_id: str, worker_index: int) -> WorkerResult:
        worker_id = f"{self.worker_prefix}-{worker_index}"
        claimed = self.delivery.claim(delivery_id)
        if claimed is None:
            return WorkerResult(delivery_id, worker_id, "not_claimed")
        assert claimed.lease_id is not None
        try:
            self.handler(claimed)
        except Exception as exc:
            return WorkerResult(delivery_id, worker_id, "failed", type(exc).__name__)
        self.delivery.ack(delivery_id, claimed.lease_id)
        return WorkerResult(delivery_id, worker_id, "acked")
