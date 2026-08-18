from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from queue import Full, Queue
from threading import Lock
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class QueueSaturatedError(RuntimeError):
    """Raised when the bounded worker queue cannot accept another task."""


class WorkerPoolClosedError(RuntimeError):
    """Raised when work is submitted after shutdown begins."""


@dataclass(frozen=True)
class WorkerPoolStats:
    capacity: int
    queued: int
    active: int
    closed: bool


class BoundedWorkerPool(Generic[T, R]):
    """Worker pool with bounded total in-flight work and explicit backpressure.

    ``max_queue`` is the total in-flight capacity: running + executor-pending
    tasks. The bookkeeping queue is deliberately separate from the executor so
    ThreadPoolExecutor's unbounded internal queue cannot create hidden backlog.
    """

    def __init__(self, max_workers: int, max_queue: int) -> None:
        if max_workers < 1 or max_queue < 1:
            raise ValueError("max_workers and max_queue must be >= 1")

        self._capacity = max_queue
        self._queue: Queue[object] = Queue(maxsize=max_queue)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = Lock()
        self._active = 0
        self._closed = False

    def __enter__(self) -> "BoundedWorkerPool[T, R]":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.shutdown()

    def submit(self, task: T, fn: Callable[[T], R]) -> Future[R]:
        """Submit one task without allowing the in-flight limit to be exceeded."""
        with self._lock:
            if self._closed:
                raise WorkerPoolClosedError("worker pool is shut down")
            try:
                self._queue.put_nowait(task)
            except Full as exc:
                raise QueueSaturatedError("worker pool in-flight capacity is full") from exc
            self._active += 1

        try:
            future = self._executor.submit(self._run, task, fn)
        except BaseException:
            # Keep capacity accounting correct even if the executor rejects
            # submission during a concurrent shutdown.
            self._release()
            raise

        future.add_done_callback(lambda _: self._release())
        return future

    @staticmethod
    def _run(task: T, fn: Callable[[T], R]) -> R:
        return fn(task)

    def _release(self) -> None:
        with self._lock:
            # The queue is used as a bounded permit ledger, not as a work
            # dispatch queue. Removing any one permit is sufficient because
            # each accepted submission owns exactly one permit.
            self._queue.get_nowait()
            self._queue.task_done()
            self._active -= 1

    def stats(self) -> WorkerPoolStats:
        with self._lock:
            queued = self._queue.qsize()
            return WorkerPoolStats(
                capacity=self._capacity,
                queued=queued,
                active=self._active,
                closed=self._closed,
            )

    def shutdown(self, wait: bool = True, cancel_pending: bool = False) -> None:
        """Stop accepting work and optionally cancel executor-pending tasks.

        Shutdown is idempotent. Pending futures cancelled by the executor still
        invoke their completion callbacks, releasing their capacity permits.
        """
        with self._lock:
            self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=cancel_pending)
