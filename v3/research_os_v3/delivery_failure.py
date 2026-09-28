from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from v3.dlq.models import DLQRecord, DLQStatus
from v3.dlq.service import DLQService
from v3.dlq.sqlite_store import SQLiteDLQStore
from .event_delivery import Delivery, DurableEventDelivery


class DeliveryFailureCoordinator:
    """Join the existing delivery lease/retry boundary to the existing DLQ.

    The event ledger remains the source of delivery state. The DLQ stores
    terminal failure evidence and never becomes a second execution queue.
    """

    def __init__(
        self,
        delivery: DurableEventDelivery,
        dlq: DLQService,
        *,
        payload_reference: Callable[[Delivery], str] | None = None,
    ) -> None:
        self.delivery = delivery
        self.dlq = dlq
        self.payload_reference = payload_reference or (
            lambda item: f"event://{item.event_id}"
        )

    def fail(
        self,
        delivery_id: str,
        lease_id: str,
        *,
        error: BaseException,
        retryable: bool = True,
    ) -> Delivery:
        current = self.delivery.get_delivery(delivery_id)
        if current is None:
            raise KeyError(delivery_id)
        if current.status == "dlq":
            return current
        if current.status != "delivering" or current.lease_id != lease_id:
            return self.delivery.fail(delivery_id, lease_id, retryable=retryable)

        terminal = (not retryable) or current.attempt >= current.max_attempts
        if terminal:
            self._ensure_dlq(current, error)
            return self.delivery.fail(delivery_id, lease_id, retryable=False)
        return self.delivery.fail(delivery_id, lease_id, retryable=True)

    def _ensure_dlq(self, delivery: Delivery, error: BaseException) -> None:
        existing = self.dlq.store.get(delivery.delivery_id)
        if existing is not None:
            return
        now = datetime.now(timezone.utc)
        record = DLQRecord(
            task_id=delivery.delivery_id,
            event_id=delivery.event_id,
            delivery_id=delivery.delivery_id,
            idempotency_key=delivery.idempotency_key,
            attempt=delivery.attempt,
            max_attempts=delivery.max_attempts,
            error_type=type(error).__name__,
            error_message=str(error)[:2000],
            payload_reference=self.payload_reference(delivery),
            failed_at=now,
            first_failed_at=now,
            last_failed_at=now,
            lease_id=delivery.lease_id,
            status=DLQStatus.AVAILABLE,
        )
        try:
            self.dlq.dead_letter(record)
        except ValueError:
            # A crash can occur after DLQ persistence and before delivery
            # finalization. Treat an existing record as the same terminal event.
            if self.dlq.store.get(record.task_id) is None:
                raise
