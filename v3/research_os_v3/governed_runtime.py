from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from v3.dlq.service import DLQService
from v3.dlq.sqlite_store import SQLiteDLQStore

from .event_delivery import Delivery, DurableEventDelivery
from .resource_lineage import (
    ConflictEvidence,
    ResourceVersion,
    ResourceVersionStore,
    release_and_reconcile_on_conflict,
)
from .worker_pool import StatelessWorkerPool, WorkerResult


class GovernedWorkflowRuntime:
    """Compose delivery, bounded workers, lineage and terminal DLQ recovery.

    This is an integration boundary only: it reuses the existing durable
    delivery ledger and existing DLQ. It does not introduce another queue.
    """

    def __init__(
        self,
        root: Path,
        *,
        concurrency: int = 4,
        max_attempts: int = 3,
        worker_prefix: str = "runner",
    ) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.delivery = DurableEventDelivery(
            root / "event_delivery.sqlite3",
        )
        self.lineage = ResourceVersionStore(root / "resource_lineage.sqlite3")
        self.dlq_store = SQLiteDLQStore(str(root / "dlq.sqlite3"))
        self.dlq = DLQService(self.dlq_store)
        self.concurrency = concurrency
        self.max_attempts = max_attempts
        self.worker_prefix = worker_prefix

    def run(
        self,
        delivery_ids: Iterable[str],
        handler: Callable[[Delivery], None],
    ) -> tuple[WorkerResult, ...]:
        def governed_handler(delivery: Delivery) -> None:
            try:
                handler(delivery)
            except Exception as exc:
                assert delivery.lease_id is not None
                self._failure(delivery, exc)
                raise

        pool = StatelessWorkerPool(
            self.delivery,
            concurrency=self.concurrency,
            handler=governed_handler,
            worker_prefix=self.worker_prefix,
        )
        return pool.run_once(delivery_ids)

    def update_resource(
        self,
        resource_id: str,
        *,
        expected_version: int,
        expected_sha256: str,
        content: object,
        release_resources: Callable[[], None],
        reconcile_delivery: Callable[[ConflictEvidence], None],
    ) -> ResourceVersion:
        return self.lineage.update(
            resource_id,
            expected_version=expected_version,
            expected_sha256=expected_sha256,
            content=content,
            on_reject=lambda evidence: release_and_reconcile_on_conflict(
                evidence,
                release_resources=release_resources,
                reconcile_delivery=reconcile_delivery,
            ),
        )

    def _failure(self, delivery: Delivery, error: BaseException) -> None:
        from .delivery_failure import DeliveryFailureCoordinator

        coordinator = DeliveryFailureCoordinator(self.delivery, self.dlq)
        coordinator.fail(
            delivery.delivery_id,
            delivery.lease_id or "",
            error=error,
            retryable=True,
        )

    def close(self) -> None:
        self.dlq_store.close()
        self.delivery.close()
