from types import SimpleNamespace
import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_execution_plane_integration import (
    P1ExecutionIntegrationError,
    assert_retry_pair,
    bind_api_execution,
    bind_v3_execution,
)

SHA = "a" * 40

def base_identity():
    return CanonicalIdentity("mission-1", "work-1", SHA)

def test_api_first_attempt_binds_existing_step():
    result = bind_api_execution(
        identity=base_identity(),
        step=SimpleNamespace(step_id="task-1", task_id="native-task-1"),
        run_id="run-1",
        attempt_id="attempt-1",
    )
    assert result.binding.plane == "api"
    assert result.binding.native_task_id == "native-task-1"
    assert result.identity.task_id == "task-1"
    assert result.identity.run_id == "run-1"
    assert result.attempt.attempt_number == 1

def test_api_retry_keeps_canonical_task_and_run_but_changes_attempt():
    first = bind_api_execution(
        identity=base_identity(),
        step=SimpleNamespace(step_id="task-1", task_id="native-task-1"),
        run_id="run-1",
        attempt_id="attempt-1",
    )
    second = bind_api_execution(
        identity=base_identity(),
        step=SimpleNamespace(step_id="task-1", task_id="native-task-2"),
        run_id="run-1",
        attempt_id="attempt-2",
        attempt_number=2,
        retry_of="attempt-1",
    )
    assert second.identity.task_id == first.identity.task_id
    assert second.identity.run_id == first.identity.run_id
    assert second.attempt.retry_of == first.attempt.attempt_id
    assert second.binding.native_task_id != first.binding.native_task_id
    assert_retry_pair(first, second)

def test_v3_retry_keeps_native_queue_task_id():
    queue = SimpleNamespace(task_id="task-1")
    research = SimpleNamespace(id="task-1")
    first = bind_v3_execution(identity=base_identity(), research_task=research, queue_task=queue, run_id="research-run-1", attempt_id="attempt-1")
    second = bind_v3_execution(identity=base_identity(), research_task=research, queue_task=queue, run_id="research-run-1", attempt_id="attempt-2", attempt_number=2, retry_of="attempt-1")
    assert first.binding.native_task_id == second.binding.native_task_id == "task-1"
    assert second.attempt.attempt_number == 2
    assert_retry_pair(first, second)

def test_v3_rejects_foreign_queue_task():
    with pytest.raises(P1ExecutionIntegrationError, match="conflicts"):
        bind_v3_execution(identity=base_identity(), research_task=SimpleNamespace(id="task-2"), queue_task=SimpleNamespace(task_id="task-2"), run_id="run-1", attempt_id="attempt-1")
