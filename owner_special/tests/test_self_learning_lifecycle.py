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


def test_lifecycle_assembles_evidence_without_mutating_candidate() -> None:
    assembler = SkillLifecycleAssembler()
    original = candidate()
    evaluation = SkillEvaluationRecord.from_candidate(original, score=0.9)
    provenance = SkillProvenance.from_candidate(
        original,
        source="observed-work",
        generated_by="self-learning",
        evaluation_score=0.9,
    )

    snapshot = assembler.start(original)
    snapshot = assembler.attach_evaluation(snapshot, evaluation)
    snapshot = assembler.attach_provenance(snapshot, provenance)
    snapshot = assembler.attach_promotion_evidence(
        snapshot,
        provenance_ref="prov:search-skill:v1",
        promotion_authority="ApprovalGate",
    )
    snapshot = assembler.attach_promotion_decision(snapshot, decision="rejected")

    assert snapshot.candidate == original
    assert snapshot.evaluation == evaluation
    assert snapshot.provenance == provenance
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


def test_rejected_decision_is_inspectable_but_not_executed() -> None:
    assembler = SkillLifecycleAssembler()
    current = candidate()
    evaluation = SkillEvaluationRecord.from_candidate(current, score=0.9)
    provenance = SkillProvenance.from_candidate(
        current,
        source="observed-work",
        generated_by="self-learning",
        evaluation_score=0.9,
    )
    snapshot = assembler.attach_provenance(
        assembler.attach_evaluation(assembler.start(current), evaluation), provenance
    )
    snapshot = assembler.attach_promotion_evidence(
        snapshot,
        provenance_ref="prov:search-skill:v1",
        promotion_authority="ApprovalGate",
    )
    rejected = assembler.attach_promotion_decision(snapshot, decision="rejected")

    assert rejected.promotion_record is not None
    assert rejected.promotion_record.normalized_decision() == "rejected"
    assert rejected.candidate.status == "candidate"
