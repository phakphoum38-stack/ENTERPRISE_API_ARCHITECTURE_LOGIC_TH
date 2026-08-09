#!/usr/bin/env python3
"""Safe experience learning for Research OS AI Brain.

This layer learns from *structured outcomes*, not hidden model reasoning and not
raw prompt/response transcripts. ActivityLedger remains the one durable event
store. Learning produces summaries and refinement proposals only; it never
changes source code, SkillDefinitions, prompts, permissions, providers, or model
weights automatically.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from v2_brain_core import ActivityLedger
from v2_secret_redactor import sanitize_request_fields


LEARNING_CONTRACT = "brain-learning-experience-phase-9"
_EXPERIENCE_EVENT = "brain.learning.experience"
_ALLOWED_STATUSES = {
    "verified",
    "failed",
    "blocked",
    "cancelled",
    "verification_failed",
}


def _bounded_text(value: Any, *, limit: int = 512) -> str:
    text = str(value or "").strip()
    safe = sanitize_request_fields(text)
    if not isinstance(safe, str):
        return ""
    return safe if len(safe) <= limit else safe[: limit - 3] + "..."


def _strings(values: Iterable[Any], *, limit: int = 64) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _bounded_text(value, limit=128)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


@dataclass(frozen=True)
class LearningPolicy:
    raw_prompt_capture: bool = False
    raw_response_capture: bool = False
    hidden_reasoning_capture: bool = False
    secret_persistence: bool = False
    self_modification: bool = False
    model_weight_update: bool = False
    automatic_skill_rewrite: bool = False
    proposals_require_review: bool = True


class LearningEngine:
    """Project experience aggregation backed only by the canonical ActivityLedger."""

    def __init__(self, ledger: ActivityLedger) -> None:
        self.ledger = ledger
        self.policy = LearningPolicy()

    def record_experience(
        self,
        *,
        session_id: str,
        task_id: str,
        status: str,
        objective: str | None = None,
        capabilities: Iterable[str] = (),
        skill_ids: Iterable[str] = (),
        tool_ids: Iterable[str] = (),
        blockers: Iterable[str] = (),
        evidence_refs: Iterable[str] = (),
        verification: Mapping[str, Any] | None = None,
        failure_category: str | None = None,
    ) -> dict[str, Any]:
        normalized_status = status.strip().casefold()
        if normalized_status not in _ALLOWED_STATUSES:
            raise ValueError(f"unsupported learning outcome status: {status}")
        if not str(session_id).strip() or not str(task_id).strip():
            raise ValueError("session_id and task_id are required")

        safe_verification = sanitize_request_fields(dict(verification or {}))
        payload = {
            "contract": LEARNING_CONTRACT,
            "task_id": _bounded_text(task_id, limit=128),
            # Objective is intentionally summarized/bounded. Raw prompt/response
            # transcripts are never accepted into the learning event contract.
            "objective_summary": _bounded_text(objective, limit=512),
            "status": normalized_status,
            "capabilities": _strings(capabilities),
            "skill_ids": _strings(skill_ids),
            "tool_ids": _strings(tool_ids),
            "blockers": _strings(blockers, limit=32),
            "evidence_refs": _strings(evidence_refs, limit=32),
            "verification": safe_verification,
            "failure_category": _bounded_text(failure_category, limit=128),
            "learning_policy": {
                "raw_prompt_capture": False,
                "raw_response_capture": False,
                "hidden_reasoning_capture": False,
                "self_modification": False,
                "model_weight_update": False,
            },
        }
        return self.ledger.record(
            _EXPERIENCE_EVENT,
            session_id=_bounded_text(session_id, limit=128),
            payload=payload,
        )

    def experiences(
        self,
        *,
        session_id: str | None = None,
        status: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        normalized = status.strip().casefold() if status else None
        if normalized and normalized not in _ALLOWED_STATUSES:
            raise ValueError(f"unsupported learning outcome status: {status}")
        events = self.ledger.list(session_id=session_id, limit=min(max(limit, 1), 500))
        result: list[dict[str, Any]] = []
        for event in events:
            if event.get("event_type") != _EXPERIENCE_EVENT:
                continue
            payload = event.get("payload")
            if not isinstance(payload, Mapping):
                continue
            if normalized and str(payload.get("status", "")).casefold() != normalized:
                continue
            result.append(dict(event))
        return result[-limit:]

    def patterns(self, *, limit: int = 500) -> dict[str, Any]:
        events = self.experiences(limit=min(max(limit, 1), 500))
        status_counts: Counter[str] = Counter()
        capability_status: dict[str, Counter[str]] = defaultdict(Counter)
        skill_status: dict[str, Counter[str]] = defaultdict(Counter)
        tool_status: dict[str, Counter[str]] = defaultdict(Counter)
        blockers: Counter[str] = Counter()
        failure_categories: Counter[str] = Counter()

        for event in events:
            payload = event.get("payload") if isinstance(event, Mapping) else None
            if not isinstance(payload, Mapping):
                continue
            status = str(payload.get("status") or "unknown")
            status_counts[status] += 1
            for capability in payload.get("capabilities") or ():
                capability_status[str(capability)][status] += 1
            for skill_id in payload.get("skill_ids") or ():
                skill_status[str(skill_id)][status] += 1
            for tool_id in payload.get("tool_ids") or ():
                tool_status[str(tool_id)][status] += 1
            blockers.update(str(item) for item in payload.get("blockers") or () if str(item).strip())
            category = str(payload.get("failure_category") or "").strip()
            if category:
                failure_categories[category] += 1

        def render(values: Mapping[str, Counter[str]]) -> dict[str, dict[str, int]]:
            return {
                key: dict(sorted(counter.items()))
                for key, counter in sorted(values.items())
            }

        return {
            "contract": LEARNING_CONTRACT,
            "experience_count": len(events),
            "status_counts": dict(sorted(status_counts.items())),
            "capability_outcomes": render(capability_status),
            "skill_outcomes": render(skill_status),
            "tool_outcomes": render(tool_status),
            "recurring_blockers": [
                {"blocker": blocker, "count": count}
                for blocker, count in blockers.most_common(20)
            ],
            "failure_categories": dict(failure_categories.most_common()),
            "hidden_reasoning_used": False,
        }

    def refinement_proposals(self, *, minimum_repeats: int = 2) -> list[dict[str, Any]]:
        if minimum_repeats < 2 or minimum_repeats > 100:
            raise ValueError("minimum_repeats must be between 2 and 100")
        patterns = self.patterns()
        proposals: list[dict[str, Any]] = []

        for item in patterns["recurring_blockers"]:
            if int(item["count"]) < minimum_repeats:
                continue
            proposals.append(
                {
                    "proposal_type": "investigate_recurring_blocker",
                    "target": item["blocker"],
                    "observations": item["count"],
                    "recommended_action": "review skill/tool contract, evidence requirements, or runbook",
                    "automatic_change": False,
                    "review_required": True,
                }
            )

        for skill_id, outcomes in patterns["skill_outcomes"].items():
            failures = sum(
                int(outcomes.get(name, 0))
                for name in ("failed", "blocked", "verification_failed")
            )
            if failures < minimum_repeats:
                continue
            proposals.append(
                {
                    "proposal_type": "review_skill_reliability",
                    "target": skill_id,
                    "observations": failures,
                    "recommended_action": "inspect failure evidence before proposing a versioned skill revision",
                    "automatic_change": False,
                    "review_required": True,
                }
            )
        return proposals

    def dashboard(self) -> dict[str, Any]:
        patterns = self.patterns()
        return {
            "contract": LEARNING_CONTRACT,
            "storage": "ActivityLedger",
            "event_type": _EXPERIENCE_EVENT,
            "experience_count": patterns["experience_count"],
            "policy": self.policy.__dict__.copy(),
            "refinement_proposal_count": len(self.refinement_proposals()),
            "self_modification": False,
            "model_weight_update": False,
        }
