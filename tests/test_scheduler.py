import pytest

from reference.runner_registry import RunnerRegistry
from reference.scheduler import NoRunnerAvailable, ReferenceScheduler, ScheduleRequest


def test_scheduler_selects_healthy_capable_runner():
    registry = RunnerRegistry()
    registry.register("runner-b", {"python"})
    registry.register("runner-a", {"python", "linux"})
    registry.set_draining("runner-b")

    selected = ReferenceScheduler(registry).select(ScheduleRequest("job-1", "python"))

    assert selected.runner_id == "runner-a"


def test_scheduler_rejects_missing_capability():
    registry = RunnerRegistry()
    registry.register("runner-a", {"node"})

    with pytest.raises(NoRunnerAvailable):
        ReferenceScheduler(registry).select(ScheduleRequest("job-1", "python"))


def test_scheduler_does_not_select_stale_runner():
    from datetime import datetime, timedelta, timezone

    registry = RunnerRegistry()
    runner = registry.register("runner-a", {"python"})
    runner.last_heartbeat = datetime.now(timezone.utc) - timedelta(minutes=5)
    registry.mark_stale(timeout_seconds=30)

    with pytest.raises(NoRunnerAvailable):
        ReferenceScheduler(registry).select(ScheduleRequest("job-1", "python"))
