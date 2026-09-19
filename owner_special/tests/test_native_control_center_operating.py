from tools.native_control_center import ControlCommand, NativeControlCenter


def test_simulation_is_observable_without_live_execution():
    center = NativeControlCenter()
    command = ControlCommand(
        command_id="CMD-001",
        intent="inspect runtime",
        mode="SIMULATION",
        target="runtime",
    )

    fingerprint = center.prepare(command)

    assert len(fingerprint) == 64
    states = [event.state for event in center.activity()]
    assert states == ["INTENT", "VALIDATE", "OBSERVE"]


def test_live_execution_requires_explicit_recording_and_evidence():
    center = NativeControlCenter()
    command = ControlCommand(
        command_id="CMD-002",
        intent="run bounded task",
        mode="LIVE",
        target="task-1",
    )
    center.prepare(command)
    center.record_authorization("CMD-002", True)
    center.record_execution("CMD-002", True, "EV-RESULT-1")

    states = [event.state for event in center.activity()]
    assert states == ["INTENT", "VALIDATE", "AUTHORIZE", "EXECUTE", "OBSERVE", "EVIDENCE", "COMPLETE"]


def test_failed_execution_enters_recovery_without_fake_completion():
    center = NativeControlCenter()
    command = ControlCommand(
        command_id="CMD-003",
        intent="run bounded task",
        mode="LIVE",
        target="task-2",
    )
    center.prepare(command)
    center.record_authorization("CMD-003", True)
    center.record_execution("CMD-003", False)

    states = [event.state for event in center.activity()]
    assert states[-1] == "RECOVER"
    assert "COMPLETE" not in states


def test_high_risk_live_command_is_fail_closed_without_human_authorization_signal():
    try:
        ControlCommand(
            command_id="CMD-004",
            intent="release artifact",
            mode="LIVE",
            risk="HIGH",
            target="release",
        )
    except ValueError as exc:
        assert "human authorization" in str(exc)
    else:
        raise AssertionError("high-risk live command must fail closed")


def test_inspector_is_descriptive_and_bounded():
    center = NativeControlCenter()
    snapshot = center.inspector(
        "evidence-1",
        "EVIDENCE",
        "VERIFIED",
        "assurance",
        "v1",
        provenance="source-1",
        evidence=("proof-1",),
        relations=tuple(f"rel-{i}" for i in range(300)),
    )

    assert snapshot.object_id == "evidence-1"
    assert len(snapshot.relations) == 256
    assert snapshot.owner == "assurance"
