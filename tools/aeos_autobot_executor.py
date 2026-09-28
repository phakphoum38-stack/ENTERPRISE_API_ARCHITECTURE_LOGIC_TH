#!/usr/bin/env python3
"""Bounded execution backend for AEOS Autobot.

The adapter executes one declared command at a time under an explicit policy.
It never grants merge authority and converts timeout/process failures into
fail-closed result states for the assurance barrier.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import time
from typing import Sequence

from tools.aeos_autobot_state_machine import ResultState


@dataclass(frozen=True)
class ExecutionPolicy:
    timeout_seconds: float = 300.0
    max_output_bytes: int = 1_000_000
    allowed_backends: frozenset[str] = frozenset({"python", "powershell"})
    merge_authority: str = "OWNER_ONLY"


@dataclass(frozen=True)
class ExecutionResult:
    state: ResultState
    returncode: int | None
    stdout: str
    stderr: str
    duration_seconds: float


def _bounded_text(value: bytes, limit: int) -> str:
    if len(value) <= limit:
        return value.decode("utf-8", errors="replace")
    return value[:limit].decode("utf-8", errors="replace") + "\n[output-truncated]"


def execute(command: Sequence[str], *, backend: str, cwd: str, policy: ExecutionPolicy, env: dict[str, str] | None = None) -> ExecutionResult:
    if not command:
        raise ValueError("empty_command")
    if backend not in policy.allowed_backends:
        raise ValueError(f"backend_not_allowed:{backend}")
    if policy.timeout_seconds <= 0:
        raise ValueError("invalid_timeout")
    if policy.max_output_bytes < 1:
        raise ValueError("invalid_output_limit")
    if not os.path.isdir(cwd):
        raise ValueError("cwd_not_found")

    started = time.monotonic()
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=child_env,
            capture_output=True,
            timeout=policy.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        stdout = _bounded_text(exc.stdout or b"", policy.max_output_bytes)
        stderr = _bounded_text(exc.stderr or b"", policy.max_output_bytes)
        return ExecutionResult(ResultState.TIMED_OUT, None, stdout, stderr, duration)
    except OSError as exc:
        duration = time.monotonic() - started
        return ExecutionResult(ResultState.INFRA_FAILED, None, "", str(exc), duration)

    duration = time.monotonic() - started
    state = ResultState.PASSED if completed.returncode == 0 else ResultState.FAILED
    return ExecutionResult(
        state,
        completed.returncode,
        _bounded_text(completed.stdout, policy.max_output_bytes),
        _bounded_text(completed.stderr, policy.max_output_bytes),
        duration,
    )
