from __future__ import annotations

import copy
import json
import re
from typing import Any


class MissionControlEvidenceError(ValueError):
    """Raised when an evidence projection cannot be safely produced."""


class MissionControlEvidenceProjection:
    """Project existing AgentRuntime evidence without creating new evidence."""

    SCHEMA = "research-os-mission-control-evidence/v1"
    MAX_RECORDS = 100
    MAX_STRING = 2048
    MAX_BYTES = 64 * 1024
    BLOCKED = re.compile(r"(?:bearer\s+|api[_-]?key|private.?key|password|credential|secret|token|javascript:|subprocess|os\.system|child_process|powershell|cmd\.exe|bash\s+-c)", re.I)

    def __init__(self, agent_runtime: Any) -> None:
        self.agent_runtime = agent_runtime

    def snapshot(self, *, owner_id: str | None = None, limit: int = 25) -> dict[str, object]:
        if limit < 1 or limit > self.MAX_RECORDS:
            raise MissionControlEvidenceError(f"limit must be between 1 and {self.MAX_RECORDS}")
        effective_owner = owner_id or self.agent_runtime.orchestrator.owner.owner_id
        runs = tuple(self.agent_runtime.list_runs(owner_id=effective_owner))
        records = [self._record(run) for run in sorted(runs, key=lambda item: item.run_id)[:limit]]
        payload: dict[str, object] = {
            "schema": self.SCHEMA,
            "owner_id": effective_owner,
            "read_only": True,
            "evidence_source": "AgentRuntime",
            "records": records,
            "record_count": len(records),
            "total_records": len(runs),
            "truncated": len(runs) > len(records),
        }
        self._validate(payload)
        return copy.deepcopy(payload)

    def _record(self, run: Any) -> dict[str, object]:
        evidence_id = getattr(run.response, "evidence_id", None) if run.response else None
        events = [event for event in run.events if event.event in {"verifying", "completed", "failed"}]
        return {
            "run_id": run.run_id,
            "owner_id": run.owner_id,
            "status": run.status.value,
            "evidence_id": evidence_id,
            "events": [{"sequence": event.sequence, "event": event.event, "status": event.status.value} for event in sorted(events, key=lambda item: item.sequence)],
        }

    def _validate(self, payload: dict[str, object]) -> None:
        if payload["read_only"] is not True or payload["evidence_source"] != "AgentRuntime":
            raise MissionControlEvidenceError("invalid evidence authority boundary")
        records = payload["records"]
        if not isinstance(records, list) or len(records) > self.MAX_RECORDS:
            raise MissionControlEvidenceError("records exceed bound")
        previous = ""
        for record in records:
            if not isinstance(record, dict):
                raise MissionControlEvidenceError("invalid evidence record")
            run_id = record.get("run_id")
            if not isinstance(run_id, str) or not run_id or run_id < previous:
                raise MissionControlEvidenceError("records must be deterministically ordered")
            previous = run_id
            for value in record.values():
                if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                    raise MissionControlEvidenceError("blocked or oversized evidence value")
        if len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")) > self.MAX_BYTES:
            raise MissionControlEvidenceError("evidence projection exceeds byte bound")
