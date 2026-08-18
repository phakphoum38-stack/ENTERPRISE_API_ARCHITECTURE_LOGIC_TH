"""Bounded worker pool for the V3 execution runtime.

The pool deliberately owns concurrency only. Queueing, lease ownership,
renewal and persistence remain injectable so the existing V3 runtime is
not duplicated or replaced.
"""
from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True)
class WorkerTask(Generic[T]):
    task_id: str
    payload: T
    attempts: int = 0


@dataclass
class WorkerResult(Generic[R]):
    task_id: str
    value: Optional[R] = None
    error: Optional[BaseException] = None
    attempts: int = 0


class BoundedWorkerPool(Generic[T, R]):
    """Fixed-size pool with bounded admission and cooperative shutdown.

    ``lease_renew`` is called while a task is executing. ``on_failure``
    can persist/requeue failed ownership using the existing lease store.
    The pool never creates a second queue or ownership system.
    """

    _STOP = object()

    def __init__(
        self,
        worker: Callable[[T], R],
        *,
        max_workers: int,
        max_queue: int,
        lease_renew: Optional[Callable[[WorkerTask[T]], None]] = None,
        on_failure: Optional[Callable[[WorkerTask[T], BaseException], None]] = None,
        renew_interval: float = 1.0,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if max_queue < 0:
            raise ValueError("max_queue must be >= 0")
        if renew_interval <= 0:
            raise ValueError("renew_interval must be > 0")
        self._worker = worker
        self._queue: queue.Queue[object] = queue.Queue(maxsize=max_queue)
        self._max_workers = max_workers
        self._lease_renew = lease_renew
        self._on_failure = on_failure
        self._renew_interval = renew_interval
        self._threads: list[threading.Thread] = []
        self._started = False
        self._stopping = False
        self._lock = threading.Lock()
        self._results: queue.Queue[WorkerResult[R]] = queue.Queue()

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            if self._stopping:
                raise RuntimeError("worker pool cannot be restarted")
            self._started = True
            for index in range(self._max_workers):
                thread = threading.Thread(
                    target=self._run,
                    name=f"v3-worker-{index + 1}",
                    daemon=True,
                )
                thread.start()
                self._threads.append(thread)

    def submit(self, task: WorkerTask[T], *, timeout: Optional[float] = None) -> None:
        with self._lock:
            if not self._started:
                raise RuntimeError("worker pool is not started")
            if self._stopping:
                raise RuntimeError("worker pool is stopping")
        self._queue.put(task, timeout=timeout)

    def shutdown(self, *, wait: bool = True, timeout: Optional[float] = None) -> None:
        with self._lock:
            if not self._started or self._stopping:
                return
            self._stopping = True
        for _ in self._threads:
            self._queue.put(self._STOP)
        if wait:
            deadline = None if timeout is None else time.monotonic() + timeout
            for thread in self._threads:
                remaining = None if deadline is None else max(0.0, deadline - time.monotonic())
                thread.join(remaining)

    def get_result(self, *, timeout: Optional[float] = None) -> WorkerResult[R]:
        return self._results.get(timeout=timeout)

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is self._STOP:
                    return
                assert isinstance(item, WorkerTask)
                task = item
                result = self._execute(task)
                self._results.put(result)
            finally:
                self._queue.task_done()

    def _execute(self, task: WorkerTask[T]) -> WorkerResult[R]:
        stop_renew = threading.Event()
        renew_thread: Optional[threading.Thread] = None
        if self._lease_renew is not None:
            renew_thread = threading.Thread(
                target=self._renew_loop,
                args=(task, stop_renew),
                name=f"lease-renewer-{task.task_id}",
                daemon=True,
            )
            renew_thread.start()
        try:
            value = self._worker(task.payload)
            return WorkerResult(task_id=task.task_id, value=value, attempts=task.attempts)
        except BaseException as exc:
            if self._on_failure is not None:
                self._on_failure(task, exc)
            return WorkerResult(task_id=task.task_id, error=exc, attempts=task.attempts)
        finally:
            stop_renew.set()
            if renew_thread is not None:
                renew_thread.join(timeout=max(self._renew_interval * 2, 0.1))

    def _renew_loop(self, task: WorkerTask[T], stop: threading.Event) -> None:
        while not stop.wait(self._renew_interval):
            try:
                assert self._lease_renew is not None
                self._lease_renew(task)
            except Exception:
                # Lease failures are surfaced to the existing ownership
                # layer on its next operation; the worker is not silently
                # given a new ownership model here.
                continue
