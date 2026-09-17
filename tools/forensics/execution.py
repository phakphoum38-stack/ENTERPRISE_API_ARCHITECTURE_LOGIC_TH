#!/usr/bin/env python3
"""Universal failure-isolation engine for bounded, reproducible forensics."""
from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Callable, Iterable, Sequence

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class Outcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Finding(str, Enum):
    CONCURRENCY_SUSPECTED = "CONCURRENCY_SUSPECTED"
    SHELL_BOUNDARY_SUSPECTED = "SHELL_BOUNDARY_SUSPECTED"
    RUNTIME_OR_COMMAND_SUSPECTED = "RUNTIME_OR_COMMAND_SUSPECTED"
    EXECUTION_BOUNDARY_SUSPECTED = "EXECUTION_BOUNDARY_SUSPECTED"
    HOLD_ISOLATE = "HOLD_ISOLATE"
    NO_ISOLATION_SIGNAL = "NO_ISOLATION_SIGNAL"


@dataclass(frozen=True)
class Observation:
    project: str
    target_sha: str
    source_sha: str | None
    probe: str
    outcome: Outcome
    return_code: int | None = None
    detail: str = ""
    workers: int | None = None
    environment: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.project or not isinstance(self.project, str):
            raise ValueError("project must be a non-empty string")
        if not SHA1_RE.fullmatch(self.target_sha):
            raise ValueError("target_sha must be an exact lowercase 40-char SHA-1")
        if self.source_sha is not None and not SHA1_RE.fullmatch(self.source_sha):
            raise ValueError("source_sha must be an exact lowercase 40-char SHA-1")
        if self.workers is not None and self.workers < 1:
            raise ValueError("workers must be >= 1")

    @property
    def fingerprint(self) -> str:
        payload = {
            "project": self.project,
            "target_sha": self.target_sha,
            "source_sha": self.source_sha,
            "probe": self.probe,
            "outcome": self.outcome.value,
            "return_code": self.return_code,
            "detail": self.detail,
            "workers": self.workers,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class IsolationReport:
    target_sha: str
    observations: tuple[Observation, ...]
    finding: Finding
    rationale: tuple[str, ...]
    signatures: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "universal-forensics-v1",
            "target_sha": self.target_sha,
            "observations": [asdict(o) | {"outcome": o.outcome.value, "fingerprint": o.fingerprint} for o in self.observations],
            "finding": self.finding.value,
            "rationale": list(self.rationale),
            "signatures": list(self.signatures),
        }


def environment_snapshot() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "os": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }


def _outcome(observations: Iterable[Observation], *, probe: str, workers: int | None = None) -> Outcome | None:
    matches = [o for o in observations if o.probe == probe and o.workers == workers]
    if len(matches) != 1:
        return None
    return matches[0].outcome


def isolate(observations: Sequence[Observation]) -> IsolationReport:
    """Derive only evidence-supported isolation findings; ambiguity stays HOLD."""
    if not observations:
        raise ValueError("at least one observation is required")
    target = observations[0].target_sha
    if any(o.target_sha != target for o in observations):
        raise ValueError("all observations must use the same target_sha")
    unique = {o.fingerprint: o for o in observations}
    obs = tuple(unique[k] for k in sorted(unique))

    direct = _outcome(obs, probe="direct")
    shell = _outcome(obs, probe="shell")
    serial = _outcome(obs, probe="platform", workers=1)
    nominal = [o for o in obs if o.probe == "platform" and o.workers is not None and o.workers > 1]
    nominal_outcomes = {o.outcome for o in nominal}

    if serial == Outcome.PASS and Outcome.FAIL in nominal_outcomes:
        finding = Finding.CONCURRENCY_SUSPECTED
        rationale = ("serial platform execution passes while a bounded concurrent execution fails",)
    elif direct == Outcome.PASS and shell == Outcome.FAIL:
        finding = Finding.SHELL_BOUNDARY_SUSPECTED
        rationale = ("direct execution passes while the shell-wrapper boundary fails",)
    elif direct == Outcome.FAIL:
        finding = Finding.RUNTIME_OR_COMMAND_SUSPECTED
        rationale = ("the direct execution probe fails; wrapper/concurrency isolation is therefore insufficient",)
    elif shell == Outcome.FAIL and serial == Outcome.FAIL:
        finding = Finding.EXECUTION_BOUNDARY_SUSPECTED
        rationale = ("shell and serial platform probes fail; the evidence localizes outside concurrency alone",)
    elif len(nominal_outcomes) > 1 or (serial is None and direct is None and shell is None):
        finding = Finding.HOLD_ISOLATE
        rationale = ("observations are incomplete or contradictory; no causal shortcut is permitted",)
    else:
        finding = Finding.NO_ISOLATION_SIGNAL
        rationale = ("available probes do not isolate a single execution boundary",)

    return IsolationReport(
        target_sha=target,
        observations=obs,
        finding=finding,
        rationale=rationale,
        signatures=tuple(sorted(unique)),
    )


def run_argv(argv: Sequence[str], *, timeout: float, cwd: str | None = None) -> tuple[Outcome, int | None, str]:
    """Run one explicit argv without a shell; classify only process outcome."""
    if not argv or any(not isinstance(part, str) or not part for part in argv):
        raise ValueError("argv must contain non-empty strings")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    try:
        completed = subprocess.run(
            list(argv), cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return Outcome.UNKNOWN, None, f"timeout:{exc.timeout}"
    except (OSError, ValueError) as exc:
        return Outcome.UNKNOWN, None, f"runner-error:{type(exc).__name__}:{exc}"
    return (Outcome.PASS if completed.returncode == 0 else Outcome.FAIL), completed.returncode, completed.stdout[-4096:]


def bounded_worker_matrix(values: Sequence[int], *, maximum: int = 16) -> tuple[int, ...]:
    """Normalize a finite worker probe set; never permits unbounded fan-out."""
    if maximum < 1:
        raise ValueError("maximum must be >= 1")
    normalized = sorted({int(v) for v in values})
    if not normalized or normalized[0] < 1 or normalized[-1] > maximum:
        raise ValueError("worker values must be within the bounded range")
    return tuple(normalized)


def report_json(report: IsolationReport) -> str:
    return json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
