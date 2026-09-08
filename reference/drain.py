from dataclasses import dataclass
from threading import Lock

from reference.runner_registry import RunnerRegistry


@dataclass(frozen=True)
class DrainResult:
    runner_id: str
    status: str
    active_jobs: int


class RunnerDrainController:
    """Reference graceful-drain controller for stateless runners."""

    def __init__(self, registry: RunnerRegistry) -> None:
        self.registry = registry
        self._lock = Lock()
        self._active_jobs: dict[str, int] = {}

    def start_job(self, runner_id: str) -> None:
        with self._lock:
            runner = self.registry.list_healthy()
            if not any(item.runner_id == runner_id for item in runner):
                raise RuntimeError("runner is not accepting new jobs")
            self._active_jobs[runner_id] = self._active_jobs.get(runner_id, 0) + 1

    def finish_job(self, runner_id: str) -> DrainResult:
        with self._lock:
            count = max(0, self._active_jobs.get(runner_id, 0) - 1)
            self._active_jobs[runner_id] = count
            status = "DRAINED" if count == 0 and runner_id not in {
                r.runner_id for r in self.registry.list_healthy()
            } else "ONLINE"
            return DrainResult(runner_id, status, count)

    def drain(self, runner_id: str) -> DrainResult:
        with self._lock:
            self.registry.set_draining(runner_id)
            active = self._active_jobs.get(runner_id, 0)
            return DrainResult(runner_id, "DRAINING", active)

    def active_jobs(self, runner_id: str) -> int:
        with self._lock:
            return self._active_jobs.get(runner_id, 0)

    def can_shutdown(self, runner_id: str) -> bool:
        with self._lock:
            return self.registry.list_healthy() == [] or (
                all(r.runner_id != runner_id for r in self.registry.list_healthy())
                and self._active_jobs.get(runner_id, 0) == 0
            )
