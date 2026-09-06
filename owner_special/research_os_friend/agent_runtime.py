from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .models import FriendRequest, FriendResponse
from .orchestrator import FriendOrchestrator


class AgentRunStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentTraceEvent:
    sequence: int
    event: str
    status: AgentRunStatus
    timestamp: str
    data: dict[str, Any]


@dataclass(frozen=True)
class AgentRun:
    run_id: str
    owner_id: str
    profile_id: str
    session_id: str
    goal: str
    status: AgentRunStatus
    events: tuple[AgentTraceEvent, ...]
    response: FriendResponse | None = None
    error: str | None = None


class AgentRuntime:
    """Thin agent-runtime lifecycle around the existing FriendOrchestrator.

    The runtime owns execution state and trace shape, while the orchestrator
    remains the authority for policy, skills, tools, memory, and providers.
    This keeps Phase 2 additive and makes a future Agents SDK adapter possible
    without replacing the current deterministic Friend path.
    """

    def __init__(self, orchestrator: FriendOrchestrator) -> None:
        self.orchestrator = orchestrator
        self._runs: dict[str, AgentRun] = {}

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _run_id(request: FriendRequest) -> str:
        import hashlib

        payload = "|".join((request.owner_id, request.profile_id, request.session_id, request.text))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]

    def _event(
        self,
        *,
        sequence: int,
        event: str,
        status: AgentRunStatus,
        data: dict[str, Any],
    ) -> AgentTraceEvent:
        return AgentTraceEvent(
            sequence=sequence,
            event=event,
            status=status,
            timestamp=self._timestamp(),
            data=data,
        )

    def run(self, request: FriendRequest) -> AgentRun:
        run_id = self._run_id(request)
        events = [
            self._event(
                sequence=1,
                event="run-created",
                status=AgentRunStatus.CREATED,
                data={"goal": request.text},
            ),
            self._event(
                sequence=2,
                event="planning",
                status=AgentRunStatus.PLANNING,
                data={
                    "requested_skills": list(request.requested_skills),
                    "requested_tools": list(request.requested_tools),
                    "complexity": request.complexity,
                    "risk": request.risk,
                },
            ),
        ]
        try:
            events.append(
                self._event(
                    sequence=3,
                    event="executing",
                    status=AgentRunStatus.EXECUTING,
                    data={},
                )
            )
            response = self.orchestrator.handle(request)
            events.append(
                self._event(
                    sequence=4,
                    event="verifying",
                    status=AgentRunStatus.VERIFYING,
                    data={
                        "evidence_id": response.evidence_id,
                        "provider": response.provider,
                        "tools": list(response.decision.selected_tools),
                        "skills": list(response.decision.selected_skills),
                    },
                )
            )
            events.append(
                self._event(
                    sequence=5,
                    event="completed",
                    status=AgentRunStatus.COMPLETED,
                    data={
                        "evidence_id": response.evidence_id,
                        "memory_items": response.memory_items,
                    },
                )
            )
            run = AgentRun(
                run_id=run_id,
                owner_id=request.owner_id,
                profile_id=request.profile_id,
                session_id=request.session_id,
                goal=request.text,
                status=AgentRunStatus.COMPLETED,
                events=tuple(events),
                response=response,
            )
        except Exception as exc:
            events.append(
                self._event(
                    sequence=4,
                    event="failed",
                    status=AgentRunStatus.FAILED,
                    data={"error": str(exc)},
                )
            )
            run = AgentRun(
                run_id=run_id,
                owner_id=request.owner_id,
                profile_id=request.profile_id,
                session_id=request.session_id,
                goal=request.text,
                status=AgentRunStatus.FAILED,
                events=tuple(events),
                error=str(exc),
            )
        self._runs[run_id] = run
        return run

    def get(self, run_id: str) -> AgentRun | None:
        return self._runs.get(run_id)

    def list_runs(self, *, owner_id: str | None = None) -> tuple[AgentRun, ...]:
        runs = tuple(self._runs.values())
        if owner_id is None:
            return runs
        return tuple(run for run in runs if run.owner_id == owner_id)
