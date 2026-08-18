from datetime import datetime, timedelta, timezone

from reference.runner_registry import RunnerRegistry


def test_register_and_heartbeat():
    registry = RunnerRegistry()
    runner = registry.register("runner-a", {"python", "linux"})
    assert runner.status == "ONLINE"
    assert "python" in runner.capabilities

    heartbeat = registry.heartbeat("runner-a")
    assert heartbeat.status == "ONLINE"


def test_stale_runner_is_marked_stale():
    registry = RunnerRegistry()
    runner = registry.register("runner-a")
    runner.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=120)

    stale = registry.mark_stale(timeout_seconds=30)

    assert [item.runner_id for item in stale] == ["runner-a"]
    assert runner.status == "STALE"


def test_draining_runner_is_not_healthy():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})
    registry.set_draining("runner-a")

    assert registry.list_healthy() == []


def test_capability_filter():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python", "linux"})
    registry.register("runner-b", {"node", "linux"})

    healthy = registry.list_healthy("python")
    assert [runner.runner_id for runner in healthy] == ["runner-a"]
