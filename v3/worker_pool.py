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


@dataclass(frozen=True)
class WorkerPoolStats:
    capacity: int
    queued: int
    active: int


class BoundedWorkerPool(Generic[T, R]):
    """Bounded, backpressure-aware worker pool.

    The queue bound includes both queued and currently executing work, so the
    pool cannot silently grow an unbounded backlog in memory.
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

    def submit(self, task: T, fn: Callable[[T], R]) -> Future[R]:
        with self._lock:
            if self._closed:
                raise RuntimeError("worker pool is shut down")
            try:
                self._queue.put_nowait(task)
            except Full as exc:
                raise QueueSaturatedError("worker pool queue is full") from exc
            self._active += 1

        future = self._executor.submit(self._run, task, fn)
        future.add_done_callback(lambda _: self._release(task))
        return future

    def _run(self, task: T, fn: Callable[[T], R]) -> R:
        return fn(task)

    def _release(self, task: T) -> None:
        with self._lock:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            finally:
                self._active -= 1

    def stats(self) -> WorkerPoolStats:
        with self._lock:
            return WorkerPoolStats(
                capacity=self._capacity,
                queued=self._queue.qsize(),
                active=self._active,
            )

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            self._closed = True
        self._executor.shutdown(wait=wait)
