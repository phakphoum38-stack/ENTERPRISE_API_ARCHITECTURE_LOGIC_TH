from dataclasses import dataclass
from queue import Queue, Empty
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class QueueMessage:
    job_id: str
    delivery_id: str
    payload: dict[str, Any]


class InMemoryQueueAdapter:
    """Reference at-least-once queue adapter for contract and integration tests."""

    def __init__(self) -> None:
        self._queue: Queue[QueueMessage] = Queue()
        self._lock = Lock()
        self._acked: set[str] = set()
        self._delivery_count = 0

    def publish(self, job_id: str, payload: dict[str, Any]) -> QueueMessage:
        with self._lock:
            self._delivery_count += 1
            message = QueueMessage(job_id, f"delivery-{self._delivery_count}", payload)
            self._queue.put(message)
            return message

    def receive(self, timeout: float = 0.0) -> QueueMessage:
        try:
            return self._queue.get(timeout=timeout)
        except Empty as exc:
            raise TimeoutError("queue is empty") from exc

    def acknowledge(self, message: QueueMessage) -> None:
        with self._lock:
            self._acked.add(message.delivery_id)
            self._queue.task_done()

    def reject(self, message: QueueMessage, requeue: bool = True) -> None:
        with self._lock:
            if requeue:
                self._delivery_count += 1
                replacement = QueueMessage(
                    message.job_id,
                    f"delivery-{self._delivery_count}",
                    message.payload,
                )
                self._queue.put(replacement)
            self._queue.task_done()

    def is_acknowledged(self, delivery_id: str) -> bool:
        with self._lock:
            return delivery_id in self._acked
