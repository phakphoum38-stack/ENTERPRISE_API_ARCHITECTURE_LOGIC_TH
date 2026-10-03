from dataclasses import dataclass

from reference.runner_registry import RunnerInfo, RunnerRegistry


class NoRunnerAvailable(Exception):
    pass


@dataclass(frozen=True)
class ScheduleRequest:
    job_id: str
    capability: str | None = None


class ReferenceScheduler:
    """Deterministic reference scheduler selecting an ONLINE capable runner."""

    def __init__(self, registry: RunnerRegistry) -> None:
        self.registry = registry

    def select(self, request: ScheduleRequest) -> RunnerInfo:
        candidates = self.registry.list_healthy(request.capability)
        if not candidates:
            raise NoRunnerAvailable(
                f"no healthy runner available for capability={request.capability!r}"
            )
        # Deterministic first-fit selection for the reference implementation.
        return sorted(candidates, key=lambda runner: runner.runner_id)[0]
