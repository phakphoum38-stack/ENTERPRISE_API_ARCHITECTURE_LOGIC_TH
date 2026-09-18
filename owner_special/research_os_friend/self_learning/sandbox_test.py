from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .observation_pipeline import LearningSandbox


@dataclass(frozen=True)
class SandboxTestSpecification:
    """Declarative checks for a sandboxed candidate; contains no executable procedure."""

    require_isolated: bool = True
    require_observation_lineage: bool = True
    require_nonempty_procedure: bool = True


@dataclass(frozen=True)
class SandboxTestResult:
    test_id: str
    sandbox_id: str
    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]


class SandboxTestBoundary:
    """Deterministic, data-only validation boundary for learning sandboxes.

    This boundary validates candidate/sandbox structure and lineage only. It never
    executes candidate procedures and has no promotion or mutation authority.
    """

    def test(
        self,
        sandbox: LearningSandbox,
        *,
        specification: SandboxTestSpecification = SandboxTestSpecification(),
    ) -> SandboxTestResult:
        checks: list[str] = []
        failures: list[str] = []

        if specification.require_isolated:
            if sandbox.isolated:
                checks.append("sandbox_isolated")
            else:
                failures.append("sandbox_not_isolated")

        if specification.require_observation_lineage:
            fingerprint = sandbox.candidate.metadata.get("observation_fingerprint", "")
            if re.fullmatch(r"[0-9a-f]{64}", fingerprint):
                checks.append("observation_lineage_bound")
            else:
                failures.append("missing_or_invalid_observation_lineage")

        if specification.require_nonempty_procedure:
            if sandbox.candidate.procedure and all(
                isinstance(step, str) and step.strip() for step in sandbox.candidate.procedure
            ):
                checks.append("procedure_declared")
            else:
                failures.append("procedure_not_declared")

        payload = json.dumps(
            {
                "sandbox_id": sandbox.sandbox_id,
                "specification": {
                    "require_isolated": specification.require_isolated,
                    "require_observation_lineage": specification.require_observation_lineage,
                    "require_nonempty_procedure": specification.require_nonempty_procedure,
                },
                "checks": checks,
                "failures": failures,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        test_id = hashlib.sha256(payload).hexdigest()

        return SandboxTestResult(
            test_id=test_id,
            sandbox_id=sandbox.sandbox_id,
            passed=not failures,
            checks=tuple(checks),
            failures=tuple(failures),
        )
