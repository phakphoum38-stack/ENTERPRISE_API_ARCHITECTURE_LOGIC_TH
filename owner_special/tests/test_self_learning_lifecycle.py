from owner_special.research_os_friend.self_learning import (
    LearnedSkillCandidate,
    SkillEvaluationRecord,
    SkillLifecycleAssembler,
    SkillLifecycleCertificate,
    SkillProvenance,
)


def candidate(version: int = 1, evidence: tuple[str, ...] = ("obs-1",), metadata: dict[str, str] | None = None) -> LearnedSkillCandidate:
    return LearnedSkillCandidate(
        name="search-skill",
        goal="find a repository fact",
        procedure=("search", "verify"),
        evidence=evidence,
        confidence=0.9,
        version=version,
        metadata=metadata or {},
    )


def assembled_snapshot():
    assembler = SkillLifecycleAssembler()
    current = candidate()
    evaluation = SkillEvaluationRecord.from_candidate(current, score=0.9)
    provenance = SkillProvenance.from_candidate(current, source="observed-work", generated_by="self-learning", evaluation_score=0.9)
    snapshot = assembler.attach_evaluation(assembler.start(current), evaluation)
    snapshot = assembler.attach_provenance(snapshot, provenance)
    snapshot = assembler.attach_promotion_evidence(snapshot, provenance_ref="prov:search-skill:v1", promotion_authority="ApprovalGate")
    return assembler, snapshot


def test_lifecycle_assembles_evidence_without_mutating_candidate() -> None:
    assembler, snapshot = assembled_snapshot()
    snapshot = assembler.attach_promotion_decision(snapshot, decision="rejected")
    assert snapshot.candidate == candidate()
    assert snapshot.evaluation is not None
    assert snapshot.provenance is not None
    assert snapshot.promotion_evidence is not None
    assert snapshot.promotion_record is not None
    assert snapshot.promotion_record.normalized_decision() == "rejected"


def test_lifecycle_rejects_wrong_evaluation_version() -> None:
    assembler = SkillLifecycleAssembler()
    snapshot = assembler.start(candidate(version=1))
    evaluation = SkillEvaluationRecord.from_candidate(candidate(version=2), score=0.9)
    try:
        assembler.attach_evaluation(snapshot, evaluation)
    except ValueError as exc:
        assert "candidate skill version" in str(exc)
    else:
        raise AssertionError("expected version mismatch")


def test_lifecycle_rejects_provenance_mismatch() -> None:
    assembler = SkillLifecycleAssembler()
    current = candidate()
    evaluation = SkillEvaluationRecord.from_candidate(current, score=0.9)
    wrong = SkillProvenance.from_candidate(candidate(evidence=("different",)), source="observed-work", generated_by="self-learning", evaluation_score=0.9)
    snapshot = assembler.attach_evaluation(assembler.start(current), evaluation)
    try:
        assembler.attach_provenance(snapshot, wrong)
    except ValueError as exc:
        assert "evaluation evidence" in str(exc)
    else:
        raise AssertionError("expected provenance mismatch")


def test_stage_locks_prevent_downstream_rewrites() -> None:
    assembler, snapshot = assembled_snapshot()
    evaluation = snapshot.evaluation
    provenance = snapshot.provenance
    assert evaluation is not None and provenance is not None
    for action, expected in (
        (lambda: assembler.attach_evaluation(snapshot, evaluation), "evaluation stage is already locked"),
        (lambda: assembler.attach_provenance(snapshot, provenance), "provenance stage is already locked"),
        (lambda: assembler.attach_promotion_evidence(snapshot, provenance_ref="changed", promotion_authority="ApprovalGate"), "promotion evidence stage is already locked"),
    ):
        try:
            action()
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError("expected lifecycle stage lock")
    decided = assembler.attach_promotion_decision(snapshot, decision="rejected")
    try:
        assembler.attach_promotion_decision(decided, decision="approved")
    except ValueError as exc:
        assert "promotion decision stage is already locked" in str(exc)
    else:
        raise AssertionError("expected decision lock")


def test_lifecycle_readiness_is_stage_bounded() -> None:
    assembler = SkillLifecycleAssembler()
    current = candidate()
    empty = assembler.start(current)
    assert not assembler.is_evaluation_ready(empty)
    assert not assembler.is_provenance_ready(empty)
    assert not assembler.is_promotion_ready(empty)
    assert not assembler.is_complete(empty)
    evaluated = assembler.attach_evaluation(empty, SkillEvaluationRecord.from_candidate(current, score=0.9))
    assert assembler.is_evaluation_ready(evaluated)
    assert not assembler.is_provenance_ready(evaluated)
    with_provenance = assembler.attach_provenance(evaluated, SkillProvenance.from_candidate(current, source="observed-work", generated_by="self-learning", evaluation_score=0.9))
    assert assembler.is_provenance_ready(with_provenance)
    ready = assembler.attach_promotion_evidence(with_provenance, provenance_ref="prov:search-skill:v1", promotion_authority="ApprovalGate")
    assert assembler.is_promotion_ready(ready)
    assert not assembler.is_complete(ready)
    assert assembler.is_complete(assembler.attach_promotion_decision(ready, decision="rejected"))


def test_complete_lifecycle_passes_integrity_and_certificate() -> None:
    assembler, snapshot = assembled_snapshot()
    complete = assembler.attach_promotion_decision(snapshot, decision="rejected")
    integrity = assembler.validate(complete)
    assert integrity.valid and integrity.stage == "promotion_decision" and integrity.errors == ()
    certificate = assembler.certify(complete)
    assert isinstance(certificate, SkillLifecycleCertificate)
    assert certificate.skill_name == "search-skill"
    assert certificate.version == 1


def test_malformed_lifecycle_snapshot_is_reported_without_mutation() -> None:
    assembler = SkillLifecycleAssembler()
    current = candidate()
    wrong_evaluation = SkillEvaluationRecord.from_candidate(candidate(version=2), score=0.9)
    malformed = type(assembler.start(current))(candidate=current, evaluation=wrong_evaluation)
    integrity = assembler.validate(malformed)
    assert not integrity.valid
    assert integrity.stage == "evaluation"
    assert "evaluation does not match candidate skill version" in integrity.errors
    try:
        assembler.certify(malformed)
    except ValueError as exc:
        assert "cannot certify invalid lifecycle" in str(exc)
    else:
        raise AssertionError("expected certificate rejection")


def test_v2_lifecycle_requires_immediate_parent_lineage() -> None:
    assembler = SkillLifecycleAssembler()
    current = candidate(version=2)
    evaluation = SkillEvaluationRecord.from_candidate(current, score=0.9)
    snapshot = assembler.attach_evaluation(assembler.start(current), evaluation)
    bad = SkillProvenance.from_candidate
    try:
        assembler.attach_provenance(snapshot, bad(current, source="feedback", generated_by="self-learning", parent_version=0, evaluation_score=0.9))
    except ValueError as exc:
        assert "parent version" in str(exc)
    else:
        raise AssertionError("expected lineage rejection")


def test_rejected_decision_remains_evidence_only() -> None:
    assembler, snapshot = assembled_snapshot()
    rejected = assembler.attach_promotion_decision(snapshot, decision="rejected")
    assert rejected.promotion_record is not None
    assert rejected.promotion_record.normalized_decision() == "rejected"
    assert rejected.candidate.status == "candidate"
