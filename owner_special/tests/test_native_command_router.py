from tools.native_command_router import NativeCommandRouter

def test_prepare_is_deterministic_and_does_not_execute() -> None:
    router = NativeCommandRouter()
    first = router.prepare(capability_id="github", action="inspect repository",
                           mode="DRY_RUN", arguments={"repo": "owner/repo"})
    second = router.prepare(capability_id="github", action="inspect repository",
                            mode="DRY_RUN", arguments={"repo": "owner/repo"})
    assert first == second
    decision = router.route(first)
    assert decision.executable is False
    assert decision.requires_human_authorization is False

def test_live_read_only_routes_to_existing_executor() -> None:
    router = NativeCommandRouter()
    command = router.prepare(capability_id="friend", action="inspect status", mode="LIVE")
    decision = router.route(command)
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
