from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from queue import Full, Queue
from threading import Condition, Lock
from typing import Any, Callable, Generic, TypeVar

T=TypeVar("T"); R=TypeVar("R"); EventSink=Callable[[str,str,dict[str,Any]],None]
class QueueSaturatedError(RuntimeError): pass
class WorkerPoolClosedError(RuntimeError): pass
class TaskTimeoutError(TimeoutError): pass
class WorkerPoolLifecycle(str,Enum): ONLINE="online"; DRAINING="draining"; DRAINED="drained"; SHUTDOWN="shutdown"
@dataclass(frozen=True)
class WorkerPoolStats: capacity:int; queued:int; active:int; timed_out:int; closed:bool; lifecycle:WorkerPoolLifecycle
class BoundedWorkerPool(Generic[T,R]):
    def __init__(self,max_workers:int,max_queue:int,event_sink:EventSink|None=None)->None:
        if max_workers<1 or max_queue<1: raise ValueError("max_workers and max_queue must be >= 1")
        self._capacity=max_queue; self._queue=Queue(maxsize=max_queue); self._executor=ThreadPoolExecutor(max_workers=max_workers); self._lock=Lock(); self._drain_condition=Condition(self._lock); self._active=0; self._timed_out=0; self._lifecycle=WorkerPoolLifecycle.ONLINE; self._event_sink=event_sink
    def __enter__(self): return self
    def __exit__(self,exc_type,exc,tb): self.shutdown()
    def submit(self,task,fn):
        with self._lock:
            if self._lifecycle is not WorkerPoolLifecycle.ONLINE: self._emit("worker.submit_rejected",task,reason=self._lifecycle.value); raise WorkerPoolClosedError("worker pool is not accepting new work")
            try:self._queue.put_nowait(task)
            except Full as exc:self._emit("worker.saturated",task,capacity=self._capacity); raise QueueSaturatedError("worker pool in-flight capacity is full") from exc
            self._active+=1
        self._emit("worker.submitted",task)
        try: future=self._executor.submit(self._run,task,fn)
        except BaseException:self._release(); self._emit("worker.submit_failed",task); raise
        future.add_done_callback(lambda _: self._release()); return future
    def run_with_timeout(self,task,fn,timeout):
        if timeout<=0: raise ValueError("timeout must be > 0")
        future=self.submit(task,fn)
        try:return future.result(timeout=timeout)
        except TimeoutError as exc:
            with self._lock:self._timed_out+=1
            future.cancel(); self._emit("worker.timeout",task,timeout=timeout); raise TaskTimeoutError(f"task timed out after {timeout:.3f}s") from exc
    def begin_drain(self):
        with self._lock:
            if self._lifecycle is WorkerPoolLifecycle.ONLINE:self._lifecycle=WorkerPoolLifecycle.DRAINING; self._emit("worker.draining","__pool__")
            return self._lifecycle
    def wait_for_drain(self,timeout=None):
        with self._drain_condition:
            if self._lifecycle is WorkerPoolLifecycle.ONLINE:self._lifecycle=WorkerPoolLifecycle.DRAINING; self._emit("worker.draining","__pool__")
            if self._lifecycle is WorkerPoolLifecycle.SHUTDOWN:return True
            if self._active==0:self._lifecycle=WorkerPoolLifecycle.DRAINED; self._emit("worker.drained","__pool__"); return True
            drained=self._drain_condition.wait_for(lambda:self._active==0,timeout=timeout)
            if drained:self._lifecycle=WorkerPoolLifecycle.DRAINED; self._emit("worker.drained","__pool__")
            return drained
    def _run(self,task,fn):
        self._emit("worker.started",task)
        try: result=fn(task)
        except BaseException as exc:self._emit("worker.failed",task,error=type(exc).__name__); raise
        self._emit("worker.completed",task); return result
    def _release(self):
        with self._drain_condition:self._queue.get_nowait(); self._queue.task_done(); self._active-=1; self._drain_condition.notify_all()
    def stats(self):
        with self._lock:return WorkerPoolStats(self._capacity,self._queue.qsize(),self._active,self._timed_out,self._lifecycle is WorkerPoolLifecycle.SHUTDOWN,self._lifecycle)
    def shutdown(self,wait=True,cancel_pending=False):
        self.begin_drain()
        if wait:self.wait_for_drain()
        self._emit("worker.shutdown","__pool__",cancel_pending=cancel_pending); self._executor.shutdown(wait=wait,cancel_futures=cancel_pending)
        with self._lock:self._lifecycle=WorkerPoolLifecycle.SHUTDOWN
    def _emit(self,event_type,task,**detail):
        if self._event_sink is None:return
        try:self._event_sink(event_type,str(task),detail)
        except Exception:return
