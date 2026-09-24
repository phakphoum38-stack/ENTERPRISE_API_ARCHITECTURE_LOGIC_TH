from pathlib import Path

from tools.lifecycle_evidence import LifecycleEvidence, LifecycleEvidenceLedger


SHA = "a" * 40


def make(state: str, **kwargs: object) -> LifecycleEvidence:
    return LifecycleEvidence.create(
        correlation_id="corr-001",
        capability_id="friend",
        action="inspect status",
        state=state,
        owner_id="owner-001",
        source_sha=SHA,
        target_sha=SHA,
        workflow_run_id="workflow-001",
        **kwargs,
    )


def test_required_evidence_fields_and_fingerprint() -> None:
    record = make("INTENT")
    assert record.event_id.startswith("ev-")
    assert record.correlation_id == "corr-001"
    assert record.source_sha == SHA
    assert record.target_sha == SHA
    assert record.workflow_run_id == "workflow-001"
    assert len(record.fingerprint) == 64
    assert len(record.evidence_sha256) == 64


def test_complete_lifecycle_validates(tmp_path: Path) -> None:
    ledger = LifecycleEvidenceLedger(tmp_path / "evidence.jsonl")
    for state in ("INTENT", "VALIDATE", "PREPARE", "AUTHORIZE", "EXECUTE", "OBSERVE", "EVIDENCE", "COMPLETE"):
        ledger.append(make(state))
    assert ledger.validate_chain(correlation_id="corr-001", expected_source_sha=SHA) == ()


def test_failed_lifecycle_requires_explicit_recovery(tmp_path: Path) -> None:
    ledger = LifecycleEvidenceLedger(tmp_path / "evidence.jsonl")
    ledger.append(make("INTENT"))
    ledger.append(make("OBSERVE"))
    ledger.append(
        make(
            "RECOVER",
            recovery_required=True,
            recovery_reason="executor-failed",
        )
    )
    assert ledger.validate_chain(correlation_id="corr-001", expected_source_sha=SHA) == ()


def test_source_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    ledger = LifecycleEvidenceLedger(tmp_path / "evidence.jsonl")
    ledger.append(make("INTENT"))
    ledger.append(make("RECOVER", recovery_required=True, recovery_reason="source-changed"))
    assert "source SHA mismatch" in ledger.validate_chain(
        correlation_id="corr-001", expected_source_sha="b" * 40
    )


def test_recovery_without_reason_is_rejected() -> None:
    try:
        make("RECOVER", recovery_required=True)
    except ValueError as exc:
        assert "recovery_reason" in str(exc)
    else:
        raise AssertionError("recovery must carry an explicit reason")


def test_module_does_not_execute_an_executor() -> None:
    assert not hasattr(LifecycleEvidenceLedger, "execute")
    assert not hasattr(LifecycleEvidenceLedger, "authorize")
