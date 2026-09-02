from __future__ import annotations

import json
import os
import threading
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_BASE_URL = "http://127.0.0.1:8765"


@dataclass
class CalendarJob:
    job_id: str
    operation: str
    status: str
    created_at: float
    updated_at: float
    result: dict[str, Any] | None = None
    error: str | None = None


class CalendarBridgeError(RuntimeError):
    pass


class ResearchOSCalendarBridge:
    """Async loopback bridge between Research OS and phakphum-calendar.

    Research OS never receives or stores Google OAuth tokens. The calendar app
    owns provider credentials and exposes only the narrow bridge contract.
    Long-running sync operations are represented by jobs so Friend does not
    hold an HTTP request open until the provider finishes.
    """

    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or os.getenv("RESEARCH_OS_CALENDAR_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = float(timeout or os.getenv("RESEARCH_OS_CALENDAR_TIMEOUT", DEFAULT_TIMEOUT_SECONDS))
        self._jobs: dict[str, CalendarJob] = {}
        self._lock = threading.Lock()

    def health(self) -> dict[str, Any]:
        try:
            payload = self._request("GET", "/v1/research-os/health")
            return {"configured": True, "reachable": True, "base_url": self.base_url, **payload}
        except Exception as exc:
            return {"configured": True, "reachable": False, "base_url": self.base_url, "error": str(exc)}

    def submit_sync(self, payload: dict[str, Any]) -> CalendarJob:
        job = CalendarJob(
            job_id=uuid.uuid4().hex,
            operation="sync",
            status="queued",
            created_at=time.time(),
            updated_at=time.time(),
        )
        with self._lock:
            self._jobs[job.job_id] = job
        thread = threading.Thread(
            target=self._run_sync,
            args=(job.job_id, dict(payload)),
            name=f"research-os-calendar-{job.job_id[:8]}",
            daemon=True,
        )
        thread.start()
        return job

    def get_job(self, job_id: str) -> CalendarJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def snapshot(self, job: CalendarJob) -> dict[str, Any]:
        return asdict(job)

    def _run_sync(self, job_id: str, payload: dict[str, Any]) -> None:
        self._update(job_id, status="running")
        try:
            result = self._request("POST", "/v1/research-os/sync", payload)
            self._update(job_id, status="completed", result=result)
        except Exception as exc:
            self._update(job_id, status="failed", error=str(exc))

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = time.time()

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, headers=headers, method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise CalendarBridgeError(f"calendar service HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise CalendarBridgeError(f"calendar service unavailable at {self.base_url}: {exc.reason}") from exc
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CalendarBridgeError("calendar service returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise CalendarBridgeError("calendar service returned a non-object response")
        return value
