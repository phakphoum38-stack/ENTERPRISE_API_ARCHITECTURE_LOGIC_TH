from __future__ import annotations

import json
import re

from tools.research_os_api.calendar_bridge import ResearchOSCalendarBridge


_BRIDGE = ResearchOSCalendarBridge()
_JOB_RE = re.compile(r"\b[a-f0-9]{32}\b")


def calendar_health(_text: str) -> str:
    return json.dumps(_BRIDGE.health(), ensure_ascii=False, sort_keys=True)


def calendar_sync(text: str) -> str:
    command = text.strip()
    if not command:
        raise ValueError("calendar sync command is required")
    job = _BRIDGE.submit_sync({"command": command})
    return json.dumps(
        {
            "job_id": job.job_id,
            "operation": job.operation,
            "status": job.status,
            "message": "Calendar sync accepted asynchronously; poll calendar.sync.status with the job_id.",
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def calendar_sync_status(text: str) -> str:
    match = _JOB_RE.search(text)
    if match is None:
        raise ValueError("calendar sync job_id is required")
    job = _BRIDGE.get_job(match.group(0))
    if job is None:
        return json.dumps(
            {"job_id": match.group(0), "status": "unknown", "message": "job is not present in this Friend process"},
            ensure_ascii=False,
            sort_keys=True,
        )
    return json.dumps(_BRIDGE.snapshot(job), ensure_ascii=False, sort_keys=True)
