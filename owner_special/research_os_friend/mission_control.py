from __future__ import annotations

from typing import Any

from .agent_runtime import AgentRun, AgentRunStatus


class MissionControl:
    """Build a read-only, owner-scoped mission view from AgentRuntime traces.

    Mission Control is presentation state only. It never executes tools,
    changes policy, mutates skills, or grants approval.
    """

    VERSION = 1
    MAX_RUNS = 100
    MAX_EVENTS_PER_RUN = 250

    def __init__(self, agent_runtime: Any) -> None:
        self.agent_runtime = agent_runtime

    @staticmethod
    def _event_view(event: Any) -> dict[str, object]:
        return {
            "sequence": event.sequence,
            "event": event.event,
            "status": event.status.value if isinstance(event.status, AgentRunStatus) else str(event.status),
            "timestamp": event.timestamp,
            "data": dict(event.data),
        }

    @classmethod
    def _run_view(cls, run: AgentRun) -> dict[str, object]:
        events = tuple(run.events[: cls.MAX_EVENTS_PER_RUN])
        return {
            "run_id": run.run_id,
            "owner_id": run.owner_id,
            "profile_id": run.profile_id,
            "session_id": run.session_id,
            "goal": run.goal,
            "status": run.status.value,
            "events": [cls._event_view(event) for event in events],
            "event_count": len(run.events),
            "truncated_events": len(run.events) > len(events),
            "evidence_id": getattr(run.response, "evidence_id", None) if run.response else None,
            "provider": getattr(run.response, "provider", None) if run.response else None,
            "error": run.error,
        }

    def snapshot(self, *, owner_id: str | None = None, limit: int = 25) -> dict[str, object]:
        if limit < 1 or limit > self.MAX_RUNS:
            raise ValueError(f"limit must be between 1 and {self.MAX_RUNS}")
        effective_owner = owner_id or self.agent_runtime.orchestrator.owner.owner_id
        runs = self.agent_runtime.list_runs(owner_id=effective_owner)
        ordered = sorted(runs, key=lambda item: item.run_id, reverse=True)[:limit]
        counts = {status.value: 0 for status in AgentRunStatus}
        for run in runs:
            counts[run.status.value] += 1
        return {
            "schema": "research-os-mission-control/v1",
            "owner_id": effective_owner,
            "read_only": True,
            "execution_authority": "FriendOrchestrator",
            "authorization_authority": "OwnerPolicy",
            "approval_authority": "ApprovalGate",
            "trace_source": "AgentRuntime",
            "runs": [self._run_view(run) for run in ordered],
            "total_runs": len(runs),
            "status_counts": counts,
            "limit": limit,
        }

    def run(self, run_id: str, *, owner_id: str | None = None) -> dict[str, object] | None:
        effective_owner = owner_id or self.agent_runtime.orchestrator.owner.owner_id
        run = self.agent_runtime.get(run_id)
        if run is None or run.owner_id != effective_owner:
            return None
        return self._run_view(run)
