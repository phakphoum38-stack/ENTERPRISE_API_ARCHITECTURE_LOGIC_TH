from pathlib import Path

from tools.native_command_router import NativeCommandRouter
from tools.validate_native_command_routing import validate

def test_contract_validates() -> None:
    assert validate(Path("current/NATIVE_COMMAND_ROUTING_CONTRACT.json")) == ()

def test_prepare_is_deterministic_and_does_not_execute() -> None:
    router = NativeCommandRouter()
    first = router.prepare(capability_id="github", action="inspect repository",
                           mode="DRY_RUN", arguments={"repo": "owner/repo"})
    second = router.prepare(capability_id="github", action="inspect repository",
                            mode="DRY_RUN", arguments={"repo": "owner/repo"})
    assert first == second
    assert router.route(first).executable is False

def test_live_read_only_routes_to_existing_executor() -> None:
    router = NativeCommandRouter()
    decision = router.route(router.prepare(capability_id="friend", action="inspect status", mode="LIVE"))
    assert decision.executable is True
    assert "FriendOrchestrator" in decision.executor_ref

def test_live_mutation_stops_at_human_boundary() -> None:
    router = NativeCommandRouter()
    command = router.prepare(capability_id="github", action="merge pull request",
                             mode="LIVE", action_class="MUTATION")
    decision = router.route(command)
    assert decision.executable is False
    assert decision.requires_human_authorization is True

def test_simulation_never_executes() -> None:
    router = NativeCommandRouter()
    command = router.prepare(capability_id="agent", action="run plan", mode="SIMULATION")
    assert router.route(command).executable is False

def test_unknown_capability_fails_closed() -> None:
    router = NativeCommandRouter()
    try:
        router.prepare(capability_id="unknown", action="inspect")
    except ValueError as exc:
        assert "unsupported capability" in str(exc)
    else:
        raise AssertionError("unknown capability must fail closed")


def test_operation_class_cannot_be_relabelled() -> None:
    router = NativeCommandRouter()
    try:
        router.prepare(
            capability_id="factory_v3",
            action="execute factory plan",
            mode="LIVE",
            action_class="READ_ONLY",
        )
    except ValueError as exc:
        assert "action class mismatch" in str(exc)
    else:
        raise AssertionError("mutation must not be relabelled as read-only")


def test_assurance_has_no_execution_operation() -> None:
    router = NativeCommandRouter()
    try:
        router.prepare(
            capability_id="assurance",
            action="inspect evidence",
            mode="LIVE",
        )
    except ValueError as exc:
        assert "unsupported action" in str(exc)
    else:
        raise AssertionError("assurance evidence authority must not become an executor")
