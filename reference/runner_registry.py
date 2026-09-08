from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import FrozenSet


@dataclass
class RunnerInfo:
    runner_id: str
    capabilities: FrozenSet[str] = field(default_factory=frozenset)
    status: str = "ONLINE"
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RunnerRegistry:
    """Reference control-plane registry for stateless runner health."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._runners: dict[str, RunnerInfo] = {}

    def register(self, runner_id: str, capabilities: set[str] | None = None) -> RunnerInfo:
        with self._lock:
            runner = self._runners.get(runner_id)
            if runner is None:
                runner = RunnerInfo(runner_id, frozenset(capabilities or set()))
                self._runners[runner_id] = runner
            else:
                runner.capabilities = frozenset(capabilities or set())
                runner.status = "ONLINE"
                runner.last_heartbeat = datetime.now(timezone.utc)
            return runner

    def heartbeat(self, runner_id: str) -> RunnerInfo:
        with self._lock:
            runner = self._runners[runner_id]
            runner.last_heartbeat = datetime.now(timezone.utc)
            runner.status = "ONLINE"
            return runner

    def mark_stale(self, timeout_seconds: int) -> list[RunnerInfo]:
        now = datetime.now(timezone.utc)
        stale: list[RunnerInfo] = []
        with self._lock:
            for runner in self._runners.values():
                age = (now - runner.last_heartbeat).total_seconds()
                if age > timeout_seconds:
                    runner.status = "STALE"
                    stale.append(runner)
        return stale

    def set_draining(self, runner_id: str) -> RunnerInfo:
        with self._lock:
            runner = self._runners[runner_id]
            runner.status = "DRAINING"
            return runner

    def list_healthy(self, capability: str | None = None) -> list[RunnerInfo]:
        with self._lock:
            return [
                r for r in self._runners.values()
                if r.status == "ONLINE" and (capability is None or capability in r.capabilities)
            ]
