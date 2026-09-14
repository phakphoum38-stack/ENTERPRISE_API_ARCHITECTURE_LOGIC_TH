#!/usr/bin/env python3
"""AEOS Master Assurance orchestrator.

Runs independent assurance controls in one invocation while preserving per-control
failure isolation and producing one machine-readable assurance manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from tools.umap_discovery import discover_all
except ModuleNotFoundError:
    from umap_discovery import discover_all

ROOT = Path(__file__).resolve().parents[1]
FAILURE_STATUSES = {"FAIL", "ERROR", "STALE", "INSUFFICIENT_EVIDENCE"}
MANIFEST_SCHEMA = "AEOS_MASTER_ASSURANCE_V2"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class ControlResult:
    control_id: str
    class_name: str
    status: str
    command: list[str]
    cwd: str
    returncode: int
    duration_seconds: float
    detail: str = ""
    evidence_id: str = ""
    failure_signature: str | None = None


def _normalize_failure_detail(detail: str) -> str:
    """Remove volatile execution metadata while preserving failure semantics."""
    normalized = " ".join(detail.split())
    normalized = re.sub(r"\baeos-[0-9]+-[0-9]+\b", "<run-id>", normalized)
    normalized = re.sub(r"\b[0-9a-f]{40}\b", "<sha>", normalized)
    normalized = re.sub(r"\b[0-9a-f]{64}\b", "<digest>", normalized)
    normalized = re.sub(r"\b(?:duration|elapsed|time)[=:][0-9.]+s?\b", lambda match: f"{match.group(0).split('=')[0].split(':')[0]}=<time>", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(?<!\w)(?:line|lineno)[=:][0-9]+", "line=<number>", normalized, flags=re.IGNORECASE)
    return normalized


def failure_signature(control_id: str, class_name: str, command: list[str], detail: str) -> str:
    """Create a stable recurrence identity independent of volatile run metadata."""
    command_identity = " ".join(command)
    semantic_detail = _normalize_failure_detail(detail)
    payload = "|".join((control_id, class_name, command_identity, semantic_detail))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{control_id}:{digest}"


def failure_event_id(control_id: str, returncode: int, detail: str) -> str:
    """Create an exact evidence identity for this particular failure event."""
    payload = f"{control_id}|{returncode}|{detail}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_control(control_id: str, class_name: str, command: list[str], control_cwd: Path | None = None) -> ControlResult:
    started = time.monotonic()
    cwd = control_cwd or ROOT
    env = None
    if control_id == "V3_REGRESSION":
        env = os.environ.copy()
        pythonpath = [str(ROOT), str(cwd)]
        existing = env.get("PYTHONPATH", "").strip()
        if existing:
            pythonpath.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    try:
        proc = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
        returncode = proc.returncode
        output = (proc.stdout + "\n" + proc.stderr).strip()
    except Exception as exc:
        returncode = 125
        output = f"control_execution_error:{type(exc).__name__}:{exc}"
    duration = round(time.monotonic() - started, 3)
    detail = output[-4000:] if output else ""
    status = "PASS" if returncode == 0 else "FAIL"
