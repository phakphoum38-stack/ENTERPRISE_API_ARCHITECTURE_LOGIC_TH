"""Concrete AEOS repository reality adapter.

This adapter observes the repository instead of accepting caller-declared
state. It binds the observed HEAD and immutable file fingerprints to the
expected baseline, contract, and policy before emitting a reality observation.
Observation remains distinct from verification and certification.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import subprocess
from typing import Iterable

from .aeos_reality_boundary import RealityObservation, bind_reality_observation


class RealityScannerError(RuntimeError):
    """Raised when repository reality cannot be observed safely."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().lower()


def scan_repository_reality(
    *,
    root: Path,
    baseline_sha: str,
    contract_path: str,
    policy_path: str,
    source_paths: Iterable[str],
    observed_at: str,
) -> RealityObservation:
    """Observe repository identity and immutable source fingerprints.

    A missing file, invalid Git identity, or stale HEAD fails closed. The
    resulting observation is still only an observation; an independent
    verifier must decide whether its facts satisfy the assurance contract.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise RealityScannerError("repository root does not exist")
    if not isinstance(baseline_sha, str) or len(baseline_sha) != 40 or any(c not in "0123456789abcdef" for c in baseline_sha):
        raise RealityScannerError("invalid baseline SHA")

    try:
        observed_sha = _git_head(root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RealityScannerError("unable to observe repository HEAD") from exc
    if observed_sha != baseline_sha:
        raise RealityScannerError("repository HEAD differs from baseline")

    contract = root / contract_path
    policy = root / policy_path
    paths = tuple(dict.fromkeys((contract_path, policy_path, *tuple(source_paths))))
    files: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        if not path.is_file():
            raise RealityScannerError(f"required reality source missing: {relative}")
        files[relative] = _sha256_file(path)

    evidence_refs = (f"git:HEAD:{observed_sha}",) + tuple(f"file:{path}:{files[path]}" for path in sorted(files))
    facts = {
        "head_sha": observed_sha,
        "contract_path": contract_path,
        "contract_sha256": files[contract_path],
        "policy_path": policy_path,
        "policy_sha256": files[policy_path],
        "source_fingerprints": {path: files[path] for path in sorted(files)},
    }
    return bind_reality_observation(
        observation_id=f"repo-reality:{observed_sha}",
        subject="repository",
        baseline_sha=baseline_sha,
        observed_sha=observed_sha,
        contract_sha256=files[contract_path],
        policy_sha256=files[policy_path],
        observed_at=observed_at,
        source="repository-reality-scanner/v1",
        status="VALID",
        facts=facts,
        evidence_refs=evidence_refs,
    )
