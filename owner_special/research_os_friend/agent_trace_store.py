from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent_runtime import AgentRun, AgentRunStatus, AgentTraceEvent


class PersistentAgentTraceStore:
    """Append-safe owner-scoped storage for high-level agent run traces.

    The store persists lifecycle state and operational evidence only. Model
    reasoning, provider credentials, and full response bodies are deliberately
    excluded from the durable trace format.
    """

    schema_version = 1

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        self._runs: dict[str, AgentRun] = {}
        self._load()

    @staticmethod
    def _event_from_dict(item: dict[str, Any]) -> AgentTraceEvent:
        return AgentTraceEvent(
            sequence=int(item["sequence"]),
            event=str(item["event"]),
            status=AgentRunStatus(item["status"]),
            timestamp=str(item["timestamp"]),
            data=dict(item.get("data", {})),
        )

    @classmethod
    def _run_from_dict(cls, item: dict[str, Any]) -> AgentRun:
        return AgentRun(
            run_id=str(item["run_id"]),
            owner_id=str(item["owner_id"]),
            profile_id=str(item["profile_id"]),
            session_id=str(item["session_id"]),
            goal=str(item["goal"]),
            status=AgentRunStatus(item["status"]),
            events=tuple(cls._event_from_dict(event) for event in item.get("events", ())),
            response=None,
            error=item.get("error"),
        )

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != self.schema_version:
            raise ValueError("invalid agent trace store schema")
        self._runs = {
            run.run_id: run
            for run in (
                self._run_from_dict(item)
                for item in payload.get("runs", [])
            )
        }

    @staticmethod
    def _serializable(run: AgentRun) -> dict[str, Any]:
        return {
            "run_id": run.run_id,
            "owner_id": run.owner_id,
            "profile_id": run.profile_id,
            "session_id": run.session_id,
            "goal": run.goal,
            "status": run.status.value,
            "events": [
                {
                    "sequence": event.sequence,
                    "event": event.event,
                    "status": event.status.value,
                    "timestamp": event.timestamp,
                    "data": event.data,
                }
                for event in run.events
            ],
            "error": run.error,
        }

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "runs": [self._serializable(run) for run in self._runs.values()],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def save(self, run: AgentRun) -> None:
        with self._lock:
            self._runs[run.run_id] = run
            self._flush()

    def get(self, run_id: str, *, owner_id: str | None = None) -> AgentRun | None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return None
            if owner_id is not None and run.owner_id != owner_id:
                return None
            return run

    def list_runs(self, *, owner_id: str) -> tuple[AgentRun, ...]:
        with self._lock:
            return tuple(
                run for run in self._runs.values()
                if run.owner_id == owner_id
            )

    def count(self, *, owner_id: str | None = None) -> int:
        with self._lock:
            if owner_id is None:
                return len(self._runs)
            return sum(run.owner_id == owner_id for run in self._runs.values())
