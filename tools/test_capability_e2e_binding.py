from pathlib import Path

from tools.capability_e2e_binding import CapabilityE2EBinding
from tools.lifecycle_evidence import LifecycleEvidenceLedger

SHA = "a" * 40


class FriendExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def snapshot(self) -> dict[str, object]:
        self.calls += 1
        return {"status": "ok", "read_only": True}


class MutatingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def ask(self, request: str) -> str:
        self.calls += 1
        return f"answered:{request}"


class FailingExecutor:
    def ask(self, request: str) -> str:
        raise RuntimeError("executor-failed")


def make_binding(tmp_path: Path) -> CapabilityE2EBinding:
    return CapabilityE2EBinding(
        ledger=LifecycleEvidenceLedger(tmp_path / "evidence.jsonl"),
        owner_id="owner-001",
        source_sha=SHA,
        target_sha=SHA,
        workflow_run_id="workflow-001",
    )


def test_friend_read_only_operation_reaches_existing_executor(tmp_path: Path) -> None:
    executor = FriendExecutor()
    result = make_binding(tmp_path).invoke(
        capability_id="friend",
        action="inspect status",
        executor=executor,
        correlation_id="corr-friend",
        authorized=True,
    )
    assert result.status == "complete"
    assert executor.calls == 1
    assert result.observation == {"status": "ok", "read_only": True}


def test_mutation_stops_at_external_authorization_boundary(tmp_path: Path) -> None:
    executor = MutatingExecutor()
    result = make_binding(tmp_path).invoke(
        capability_id="friend",
        action="ask friend",
        executor=executor,
        args=("hello",),
        correlation_id="corr-mutation",
        authorized=False,
    )
    assert result.status == "recover"
    assert executor.calls == 0
    assert "authorization" in (result.recovery_reason or "").lower()


def test_executor_failure_is_terminal_recovery(tmp_path: Path) -> None:
    result = make_binding(tmp_path).invoke(
        capability_id="friend",
        action="ask friend",
        executor=FailingExecutor(),
        args=("hello",),
        correlation_id="corr-failure",
        authorized=True,
    )
    assert result.status == "recover"
    assert make_binding(tmp_path).ledger.validate_chain(
        correlation_id="corr-failure", expected_source_sha=SHA
    ) == ()


def test_assurance_cannot_be_promoted_to_execution(tmp_path: Path) -> None:
    class AssuranceExecutor:
        pass

    result = make_binding(tmp_path).invoke(
        capability_id="assurance",
        action="record evidence",
        executor=AssuranceExecutor(),
        correlation_id="corr-assurance",
        authorized=True,
    )
    assert result.status == "recover"
    assert "unsupported action" in (result.recovery_reason or "")


def test_unknown_executor_method_fails_closed(tmp_path: Path) -> None:
    result = make_binding(tmp_path).invoke(
        capability_id="github",
        action="inspect repository",
        executor=object(),
        correlation_id="corr-github",
        authorized=True,
    )
    assert result.status == "recover"
    assert "canonical method" in (result.recovery_reason or "")


def test_factory_binding_uses_existing_execute_method(tmp_path: Path) -> None:
    class Factory:
        def execute(self, plan: str) -> str:
            return f"executed:{plan}"

    result = make_binding(tmp_path).invoke(
        capability_id="factory_v3",
        action="execute factory plan",
        executor=Factory(),
        args=("plan-1",),
        correlation_id="corr-factory",
        authorized=True,
    )
    assert result.status == "complete"
    assert result.observation == "executed:plan-1"
