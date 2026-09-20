#!/usr/bin/env python3
"""Mechanical execution adapter for canonical GitHub Actions workflow bindings.

This layer performs I/O only after the Control Center has prepared and, for LIVE
execution, authorized a command. It does not grant authority, mutate policy,
merge PRs, or create a second workflow engine.

The default implementation uses the existing GitHub CLI (gh api). Tests can
inject a runner so dispatch/discovery/wait behavior is deterministic and
side-effect free.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence

from .workflow_resolver import ResolvedWorkflow

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class WorkflowExecutionError(RuntimeError):
    """Fail-closed execution/observation error."""


@dataclass(frozen=True)
class WorkflowExecutionRequest:
    resolution: ResolvedWorkflow
    repository: str
    target_sha: str
    mode: str = "LIVE"
    inputs: Mapping[str, str] | None = None
    authorized: bool = False
    discovery_timeout_seconds: int = 120
    completion_timeout_seconds: int = 3600
    poll_seconds: float = 3.0

    def __post_init__(self) -> None:
        if not self.repository.strip():
            raise ValueError("repository is required")
        if not SHA256_RE.fullmatch(self.target_sha):
            raise ValueError("target_sha must be a canonical 64-character SHA-256 value")
        if self.mode not in {"LIVE", "SIMULATION", "DRY_RUN", "REPLAY"}:
            raise ValueError(f"unsupported execution mode: {self.mode}")
        if self.discovery_timeout_seconds < 1 or self.completion_timeout_seconds < 1:
            raise ValueError("execution timeouts must be positive")
        if self.poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")
        object.__setattr__(self, "inputs", dict(self.inputs or {}))


@dataclass(frozen=True)
class WorkflowExecutionObservation:
    command_id: str
    resolution_fingerprint: str
    repository: str
    workflow_file: str
    run_id: str | None
    target_sha: str
    observed_head_sha: str | None
    status: str
    conclusion: str | None
    html_url: str | None
    dispatch_ref: str
    input_keys: tuple[str, ...]
    observation_fingerprint: str


Runner = Callable[[Sequence[str], bytes | None], bytes]


def observation_fingerprint(observation: WorkflowExecutionObservation) -> str:
    payload = {
        "command_id": observation.command_id,
        "resolution_fingerprint": observation.resolution_fingerprint,
        "repository": observation.repository,
        "workflow_file": observation.workflow_file,
        "run_id": observation.run_id,
        "target_sha": observation.target_sha,
        "observed_head_sha": observation.observed_head_sha,
        "status": observation.status,
        "conclusion": observation.conclusion,
        "html_url": observation.html_url,
        "dispatch_ref": observation.dispatch_ref,
        "input_keys": list(observation.input_keys),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class GitHubWorkflowExecutionAdapter:
    """Dispatch and observe one already-resolved workflow."""

    def __init__(
        self,
        *,
        runner: Runner | None = None,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.time,
    ) -> None:
        self._runner = runner or self._gh_runner
        self._sleep = sleep
        self._now = now

    @staticmethod
    def _gh_runner(argv: Sequence[str], payload: bytes | None) -> bytes:
        command = ["gh", "api", *argv]
        if payload is not None:
            command.extend(["--method", "POST", "--input", "-"])
            completed = subprocess.run(
                command,
                input=payload,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        else:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise WorkflowExecutionError(
                f"gh api failed with exit {completed.returncode}: {detail}"
            )
        return completed.stdout

    @staticmethod
    def _workflow_name(resolution: ResolvedWorkflow) -> str:
        return resolution.workflow.file.rsplit("/", 1)[-1]

    @staticmethod
    def _dispatch_payload(
        resolution: ResolvedWorkflow,
        target_sha: str,
        inputs: Mapping[str, str],
    ) -> dict[str, Any]:
        declared = set(resolution.input_keys)
        unknown = sorted(set(inputs) - declared)
        if unknown:
            raise WorkflowExecutionError(
                f"workflow input keys are not declared: {', '.join(unknown)}"
            )

        final_inputs = dict(inputs)
        if "target_sha" in declared:
            final_inputs.setdefault("target_sha", target_sha)
        elif "ref" in declared:
            final_inputs.setdefault("ref", target_sha)

        return {"ref": target_sha, "inputs": final_inputs}

    def execute(self, request: WorkflowExecutionRequest) -> WorkflowExecutionObservation:
        resolution = request.resolution
        if resolution.target_sha is not None and resolution.target_sha != request.target_sha:
            raise WorkflowExecutionError(
                "resolved target SHA differs from execution request target SHA"
            )

        if request.mode != "LIVE":
            return self._non_live_observation(request)

        if not request.authorized:
            raise WorkflowExecutionError(
                "LIVE workflow execution requires authorization from the Control Center"
            )

        payload = self._dispatch_payload(
            resolution,
            request.target_sha,
            request.inputs or {},
        )
        workflow_file = self._workflow_name(resolution)
        encoded_workflow = workflow_file.replace("%", "%25").replace("/", "%2F")
        dispatch_path = (
            f"repos/{request.repository}/actions/workflows/"
            f"{encoded_workflow}/dispatches"
        )
        started_at = self._now()
        self._runner(
            [dispatch_path],
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
        )

        run = self._discover_run(
            repository=request.repository,
            workflow_file=workflow_file,
            target_sha=request.target_sha,
            started_at=started_at,
            timeout=request.discovery_timeout_seconds,
            poll=request.poll_seconds,
        )
        run_id = str(run["id"])
        observed_sha = str(run.get("head_sha") or "")
        if observed_sha != request.target_sha:
            raise WorkflowExecutionError(
                f"exact-head verification failed: expected {request.target_sha}, "
                f"observed {observed_sha or 'missing'}"
            )

        final = self._wait_for_completion(
            repository=request.repository,
            run_id=run_id,
            target_sha=request.target_sha,
            timeout=request.completion_timeout_seconds,
            poll=request.poll_seconds,
        )

        status = str(final.get("status") or "unknown")
        conclusion = final.get("conclusion")
        observation = WorkflowExecutionObservation(
            command_id=resolution.command_id,
            resolution_fingerprint=resolution.resolution_fingerprint,
            repository=request.repository,
            workflow_file=workflow_file,
            run_id=run_id,
            target_sha=request.target_sha,
            observed_head_sha=str(final.get("head_sha") or ""),
            status=status,
            conclusion=str(conclusion) if conclusion is not None else None,
            html_url=final.get("html_url"),
            dispatch_ref=request.target_sha,
            input_keys=tuple(sorted(payload["inputs"])),
            observation_fingerprint="",
        )
        return WorkflowExecutionObservation(
            **{
                **observation.__dict__,
                "observation_fingerprint": observation_fingerprint(observation),
            }
        )

    def _discover_run(
        self,
        *,
        repository: str,
        workflow_file: str,
        target_sha: str,
        started_at: float,
        timeout: int,
        poll: float,
    ) -> Mapping[str, Any]:
        encoded = workflow_file.replace("%", "%25").replace("/", "%2F")
        path = (
            f"repos/{repository}/actions/workflows/{encoded}/runs"
            "?event=workflow_dispatch&per_page=30"
        )
        deadline = self._now() + timeout
        while self._now() < deadline:
            data = json.loads(self._runner([path], None) or b"{}")
            candidates = []
            for run in data.get("workflow_runs", []):
                if run.get("event") != "workflow_dispatch":
                    continue
                if run.get("head_sha") != target_sha:
                    continue
                created = _parse_time(run.get("created_at"))
                if created is not None and created + 30 >= started_at:
                    candidates.append(run)
            if candidates:
                return max(candidates, key=lambda item: int(item.get("id", 0)))
            self._sleep(poll)
        raise WorkflowExecutionError(
            f"workflow run discovery timed out for {workflow_file} at {target_sha}"
        )

    def _wait_for_completion(
        self,
        *,
        repository: str,
        run_id: str,
        target_sha: str,
        timeout: int,
        poll: float,
    ) -> Mapping[str, Any]:
        path = f"repos/{repository}/actions/runs/{run_id}"
        deadline = self._now() + timeout
        while self._now() < deadline:
            current = json.loads(self._runner([path], None) or b"{}")
            current_sha = current.get("head_sha")
            if current_sha and current_sha != target_sha:
                raise WorkflowExecutionError(
                    f"workflow run SHA changed: expected {target_sha}, observed {current_sha}"
                )
            if current.get("status") == "completed":
                return current
            self._sleep(poll)
        raise WorkflowExecutionError(
            f"workflow run {run_id} did not complete before timeout"
        )

    @staticmethod
    def _non_live_observation(
        request: WorkflowExecutionRequest,
    ) -> WorkflowExecutionObservation:
        resolution = request.resolution
        observation = WorkflowExecutionObservation(
            command_id=resolution.command_id,
            resolution_fingerprint=resolution.resolution_fingerprint,
            repository=request.repository,
            workflow_file=resolution.workflow.file.rsplit("/", 1)[-1],
            run_id=None,
            target_sha=request.target_sha,
            observed_head_sha=None,
            status=f"{request.mode.lower()}_not_executed",
            conclusion=None,
            html_url=None,
            dispatch_ref=request.target_sha,
            input_keys=tuple(sorted(request.inputs or {})),
            observation_fingerprint="",
        )
        return WorkflowExecutionObservation(
            **{
                **observation.__dict__,
                "observation_fingerprint": observation_fingerprint(observation),
            }
        )


def _parse_time(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        ).timestamp()
    except ValueError:
        return None


__all__ = [
    "GitHubWorkflowExecutionAdapter",
    "WorkflowExecutionError",
    "WorkflowExecutionObservation",
    "WorkflowExecutionRequest",
    "observation_fingerprint",
]
