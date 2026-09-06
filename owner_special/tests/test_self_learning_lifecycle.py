from owner_special.research_os_friend.self_learning import (
    LearnedSkillCandidate,
    SkillEvaluationRecord,
    SkillLifecycleAssembler,
    SkillProvenance,
)


def candidate(version: int = 1, evidence: tuple[str, ...] = ("obs-1",)) -> LearnedSkillCandidate:
    return LearnedSkillCandidate(
        name="search-skill",
        goal="find a repository fact",
        procedure=("search", "verify"),
        evidence=evidence,
        confidence=0.9,
        version=version,
    )


def assembled_snapshot():
    assembler = SkillLifecycleAssembler()
    current = candidate()
    evaluation = SkillEvaluationRecord.from_candidate(current, score=0.9)
    provenance = SkillProvenance.from_candidate(
        current,
        source="observed-work",
        generated_by="self-learning",
        evaluation_score=0.9,
    )
    snapshot = assembler.attach_evaluation(assembler.start(current), evaluation)
    snapshot = assembler.attach_provenance(snapshot, provenance)
    snapshot = assembler.attach_promotion_evidence(
        snapshot,
        provenance_ref="prov:search-skill:v1",
        promotion_authority="ApprovalGate",
    )
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
    current = candidate(version=1)
    evaluation = SkillEvaluationRecord.from_candidate(current, score=0.9)
    wrong = SkillProvenance.from_candidate(
        candidate(version=1, evidence=("different",)),
        source="observed-work",
        generated_by="self-learning",
        evaluation_score=0.9,
    )
    snapshot = assembler.attach_evaluation(assembler.start(current), evaluation)

    try:
        assembler.attach_provenance(snapshot, wrong)
    except ValueError as exc:
        assert "evaluation evidence" in str(exc)
    else:
        raise AssertionError("expected provenance mismatch")


def test_promotion_requires_evidence_and_validates_decision() -> None:
    assembler = SkillLifecycleAssembler()
    snapshot = assembler.start(candidate())

    try:
        assembler.attach_promotion_decision(snapshot, decision="approved")
    except ValueError as exc:
        assert "promotion evidence" in str(exc)
    else:
        raise AssertionError("expected missing evidence")


def test_stage_locks_prevent_downstream_rewrites() -> None:
    assembler, snapshot = assembled_snapshot()
    evaluation = snapshot.evaluation
    provenance = snapshot.provenance
    assert evaluation is not None
    assert provenance is not None

    try:
        assembler.attach_evaluation(snapshot, evaluation)
    except ValueError as exc:
        assert "evaluation stage is already locked" in str(exc)
    else:
        raise AssertionError("expected evaluation lock")

    try:
        assembler.attach_provenance(snapshot, provenance)
    except ValueError as exc:
        assert "provenance stage is already locked" in str(exc)
    else:
        raise AssertionError("expected provenance lock")

    try:
        assembler.attach_promotion_evidence(
            snapshot,
            provenance_ref="prov:search-skill:v1-new",
            promotion_authority="ApprovalGate",
        )
    except ValueError as exc:
        assert "promotion evidence stage is already locked" in str(exc)
    else:
        raise AssertionError("expected promotion evidence lock")

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

    evaluation = SkillEvaluationRecord.from_candidate(current, score=0.9)
    evaluated = assembler.attach_evaluation(empty, evaluation)
    assert assembler.is_evaluation_ready(evaluated)
    assert not assembler.is_provenance_ready(evaluated)

    provenance = SkillProvenance.from_candidate(
        current,
        source="observed-work",
        generated_by="self-learning",
        evaluation_score=0.9,
    )
    with_provenance = assembler.attach_provenance(evaluated, provenance)
    assert assembler.is_provenance_ready(with_provenance)
    assert not assembler.is_promotion_ready(with_provenance)

    ready = assembler.attach_promotion_evidence(
        with_provenance,
        provenance_ref="prov:search-skill:v1",
        promotion_authority="ApprovalGate",
    )
    assert assembler.is_promotion_ready(ready)
    assert not assembler.is_complete(ready)
    complete = assembler.attach_promotion_decision(ready, decision="rejected")
    assert assembler.is_complete(complete)


def test_complete_lifecycle_passes_integrity_validation() -> None:
    assembler, snapshot = assembled_snapshot()
    complete = assembler.attach_promotion_decision(snapshot, decision="rejected")

    integrity = assembler.validate(complete)
    assert integrity.valid
    assert integrity.stage == "promotion_decision"
    assert integrity.errors == ()


def test_malformed_lifecycle_snapshot_is_reported_without_mutation() -> None:
    assembler = SkillLifecycleAssembler()
    current = candidate()
    wrong_evaluation = SkillEvaluationRecord.from_candidate(candidate(version=2), score=0.9)
    malformed = type(assembler.start(current))(
        candidate=current,
        evaluation=wrong_evaluation,
    )

    integrity = assembler.validate(malformed)
    assert not integrity.valid
    assert integrity.stage == "evaluation"
    assert "evaluation does not match candidate skill version" in integrity.errors


def test_rejected_decision_remains_evidence_only() -> None:
    assembler, snapshot = assembled_snapshot()
    rejected = assembler.attach_promotion_decision(snapshot, decision="rejected")

    assert rejected.promotion_record is not None
    assert rejected.promotion_record.normalized_decision() == "rejected"
    assert rejected.candidate.status == "candidate"
