import pytest

from reference.drain import RunnerDrainController
from reference.runner_registry import RunnerRegistry


def test_draining_runner_stops_new_jobs_but_allows_active_job_to_finish():
    registry = RunnerRegistry()
    registry.register("runner-a", {"python"})
    controller = RunnerDrainController(registry)

    controller.start_job("runner-a")
    result = controller.drain("runner-a")

    assert result.status == "DRAINING"
    assert result.active_jobs == 1
    with pytest.raises(RuntimeError):
        controller.start_job("runner-a")

    finished = controller.finish_job("runner-a")
    assert finished.active_jobs == 0
    assert controller.can_shutdown("runner-a")


def test_online_runner_can_accept_jobs():
    registry = RunnerRegistry()
    registry.register("runner-a")
    controller = RunnerDrainController(registry)

    controller.start_job("runner-a")
    assert controller.active_jobs("runner-a") == 1
