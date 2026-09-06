from __future__ import annotations

from dataclasses import dataclass

from .evaluation_history import SkillEvaluationRecord
from .feedback import SkillFeedback
from .models import LearnedSkillCandidate
from .versioning import SkillVersionProposal, propose_next_version


@dataclass(frozen=True)
class SkillRevisionProposal:
    """Immutable proposal for a learned-skill revision; it never promotes or mutates state."""

    skill_name: str
    version: int
    parent_version: int
    change_reason: str
    feedback_refs: tuple[str, ...] = ()


def propose_revision(
    current: LearnedSkillCandidate,
    feedback: tuple[SkillFeedback, ...],
    *,
    change_reason: str = "feedback-driven-revision",
) -> SkillRevisionProposal:
    """Create a deterministic next-version proposal bound to the current version."""
    for item in feedback:
        if item.skill_name != current.name or item.version != current.version:
            raise ValueError("feedback must match the current skill version")

    version_proposal: SkillVersionProposal = propose_next_version(
        LearnedSkillCandidate(
            name=current.name,
            goal=current.goal,
            procedure=current.procedure,
            evidence=current.evidence,
            confidence=current.confidence,
            status=current.status,
            version=current.version,
            metadata=current.metadata,
        ),
        current,
        change_reason=change_reason,
    )
    return SkillRevisionProposal(
        skill_name=current.name,
        version=version_proposal.version,
        parent_version=current.version,
        change_reason=version_proposal.change_reason,
        feedback_refs=tuple(item.evidence[0] for item in feedback if item.evidence),
    )


def bind_revision_evaluation(
    candidate: LearnedSkillCandidate,
    proposal: SkillRevisionProposal,
    *,
    score: float,
    feedback: tuple[SkillFeedback, ...] = (),
) -> SkillEvaluationRecord:
    """Bind an evaluation to the proposed revision without promoting it."""
    if candidate.name != proposal.skill_name or candidate.version != proposal.version:
        raise ValueError("candidate must match revision proposal")
    if candidate.metadata.get("parent_version") != str(proposal.parent_version):
        raise ValueError("candidate parent_version must match revision proposal")
    for item in feedback:
        if item.skill_name != proposal.skill_name or item.version != proposal.parent_version:
            raise ValueError("revision feedback must refer to the parent skill version")
    return SkillEvaluationRecord.from_candidate(candidate, score=score, feedback=feedback)
