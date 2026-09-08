from dataclasses import dataclass
from typing import Any, Callable

from reference.jobstore import InMemoryJobStore, LeaseConflict
from reference.queue import InMemoryQueueAdapter, QueueMessage


@dataclass
class ExecutionResult:
    job_id: str
    status: str
    error: str | None = None


class ReferenceExecutionLoop:
    """Small end-to-end reference loop joining queue delivery and JobStore leases."""

    def __init__(self, store: InMemoryJobStore, queue: InMemoryQueueAdapter) -> None:
        self.store = store
        self.queue = queue

    def submit(self, workflow_id: str, idempotency_key: str, payload: dict[str, Any]):
        job = self.store.create(workflow_id, idempotency_key, payload)
        self.queue.publish(job.job_id, payload)
        return job

    def process_once(self, runner_id: str, handler: Callable[[dict[str, Any]], Any]) -> ExecutionResult:
        message = self.queue.receive()
        try:
            job = self.store.claim(message.job_id, runner_id)
            handler(message.payload)
            self.store.complete(job.job_id, job.lease_id)
            self.queue.acknowledge(message)
            return ExecutionResult(job.job_id, "SUCCEEDED")
        except LeaseConflict as exc:
            self.queue.reject(message, requeue=False)
            return ExecutionResult(message.job_id, "CONFLICT", str(exc))
        except Exception as exc:
            # The lease owner records failure; queue delivery is requeued for retry.
            try:
                self.store.fail(job.job_id, job.lease_id)
            except (UnboundLocalError, LeaseConflict):
                pass
            self.queue.reject(message, requeue=True)
            return ExecutionResult(message.job_id, "FAILED", str(exc))
