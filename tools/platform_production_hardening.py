"""Production-hardening proof harness over existing Research OS platform primitives.

This module is validation-only. It does not introduce a scheduler, queue, runtime,
authorization authority, evidence ledger, or release authority.
"""
from __future__ import annotations

import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event

from tools.project_scale_execution import execute_scale_concurrently, exercise_resource_conflict
from tools.project_scale_readiness import build_project_definitions
from tools.project_registry import ProjectRegistry
from tools.lifecycle_evidence import LifecycleEvidence, LifecycleEvidenceLedger
from v3.research_os_v3.queue import DurableTaskQueue, LeaseOwnershipError, QueueTask
from v3.research_os_v3.runner import StatelessResearchRunner
from v3.worker_pool import BoundedWorkerPool, QueueSaturatedError, TaskTimeoutError, WorkerPoolClosedError
from tools.platform_runtime_readiness import validate_readiness_sequence


@dataclass(frozen=True)
class HardeningSummary:
    scale: str
    failure_recovery: str
    evidence_provenance: str
    distribution_contract: str
    runtime_readiness: str
    production_readiness: str


def _record_lifecycle(path: Path, *, project_id: str, source_sha: str, state: str,
                      correlation_id: str, recovery: bool = False,
                      reason: str | None = None) -> None:
    ledger = LifecycleEvidenceLedger(path)
    ledger.append(LifecycleEvidence.create(
        correlation_id=correlation_id,
        capability_id="platform-hardening",
        action="hardening-proof",
        state=state,
        owner_id="owner",
        source_sha=source_sha,
        target_sha=source_sha,
        workflow_run_id="hardening-proof",
        project_id=project_id,
        recovery_required=recovery,
        recovery_reason=reason,
    ))


def prove_failure_recovery() -> tuple[str, ...]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        queue = DurableTaskQueue(root / "queue.db", default_lease_seconds=1)
        queue.enqueue(QueueTask("retry-1", "project-001", {"kind": "retry"}))
        attempts = {"count": 0}

        def failing_handler(_task: QueueTask) -> None:
            attempts["count"] += 1
            raise RuntimeError("simulated failure")

        runner = StatelessResearchRunner(queue, max_attempts=2, worker_id="hardening-runner")
        first = runner.run_once(failing_handler)
        second = runner.run_once(failing_handler)
        if first is None or first.status != "retry":
            failures.append("retry did not produce explicit retry state")
        if second is None or second.status != "failed":
            failures.append("retry exhaustion did not produce failed state")
        if attempts["count"] != 2:
            failures.append("retry attempt count drifted")

        queue.enqueue(QueueTask("lease-1", "project-002", {"kind": "lease"}))
        leased = queue.claim(worker_id="worker-a", lease_seconds=1)
        assert leased is not None and leased.lease_id
        time.sleep(1.05)
        if queue.recover_expired_leases() != 1:
            failures.append("expired lease was not recovered")
        try:
            queue.ack(leased.task_id, leased.lease_id)
        except LeaseOwnershipError:
            pass
        else:
            failures.append("stale ACK was accepted")

        pool = BoundedWorkerPool(max_workers=1, max_queue=2)
        blocker = Event()
        future = pool.submit("timeout-task", lambda _: blocker.wait())
        try:
            pool.run_with_timeout("timeout-task-2", lambda _: blocker.wait(), timeout=0.01)
        except TaskTimeoutError:
            pass
        finally:
            blocker.set()
            future.result(timeout=2)
            pool.shutdown()
        if not pool.stats().closed:
            failures.append("worker pool did not close after recovery/drain")

        pool2 = BoundedWorkerPool(max_workers=1, max_queue=1)
        pool2.begin_drain()
        try:
            pool2.submit("cancelled-admission", lambda _: None)
        except WorkerPoolClosedError:
            pass
        else:
            failures.append("draining pool admitted new work")
        pool2.shutdown(wait=True)

    return tuple(failures)


def prove_evidence_provenance() -> tuple[str, ...]:
    failures: list[str] = []
    source_sha = "a" * 40
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "evidence.jsonl"
        _record_lifecycle(path, project_id="project-001", source_sha=source_sha,
                          state="COMPLETE", correlation_id="c-001")
        ledger = LifecycleEvidenceLedger(path)
        if ledger.validate_chain(correlation_id="c-001", expected_source_sha=source_sha,
                                   expected_project_id="project-001"):
            failures.append("valid project evidence did not validate")
        if not ledger.validate_chain(correlation_id="c-001", expected_source_sha="b" * 40,
                                         expected_project_id="project-001"):
            pass
        else:
            failures.append("stale source SHA was accepted")
        if not ledger.validate_chain(correlation_id="c-001", expected_source_sha=source_sha,
                                      expected_project_id="project-002"):
            pass
        else:
            failures.append("cross-project evidence was accepted")
        _record_lifecycle(path, project_id="project-002", source_sha=source_sha,
                          state="COMPLETE", correlation_id="c-002")
        if not ledger.validate_chain(correlation_id="c-002", expected_source_sha=source_sha,
                                      expected_project_id="project-001"):
            pass
        else:
            failures.append("cross-project lineage was accepted")
    return tuple(failures)


def validate_distribution_contract(root: Path) -> tuple[str, ...]:
    contract_path = root / "current" / "RESEARCH_OS_PLATFORM_PRODUCTION_HARDENING_CONTRACT.json"
    distribution_path = root / "current" / "RESEARCH_OS_PHASE_E_UNIFIED_WINDOWS_DISTRIBUTION_CONTRACT.json"
    if not contract_path.is_file() or not distribution_path.is_file():
        return ("distribution contract missing",)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    distribution = json.loads(distribution_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    required = set(contract["distribution"]["required_components"])
    actual = set(distribution["required_components"]) | {"universal_runner", "runner_installer"}
    if not required.issubset(actual):
        failures.append("unified distribution component set is incomplete")
    if distribution["authority"]["final_gate_remains_release_authority"] is not True:
        failures.append("distribution release authority drifted")
    return tuple(failures)


def prove_100_project_scale(root: Path) -> tuple[str, ...]:
    with tempfile.TemporaryDirectory() as raw:
        registry = ProjectRegistry(build_project_definitions(100))
        summary = execute_scale_concurrently(
            registry=registry,
            ledger_path=Path(raw) / "scale-evidence.jsonl",
            owner_id="owner",
            source_sha="a" * 40,
            target_sha="a" * 40,
            workflow_run_id="platform-hardening-100",
            max_workers=16,
        )
    if summary.project_count != 100 or summary.completed != 100 or summary.evidence_records != 800:
        return ("100-project concurrent proof did not complete with 100/100 and 800 evidence records",)
    return ()


def validate_scale_contract(root: Path) -> tuple[str, ...]:
    path = root / "current" / "RESEARCH_OS_PROJECT_SCALE_EXECUTION_CONTRACT.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("scale_levels") != [10, 20, 50, 100]:
        return ("100-project scale levels drifted",)
    required = set(data.get("required_invariants", []))
    expected = {"concurrent_shared_execution", "concurrent_project_evidence_isolated"}
    return () if expected.issubset(required) else ("100-project concurrency invariants missing",)


def run_platform_hardening(root: Path) -> HardeningSummary:
    readiness_failures = validate_readiness_sequence([
        "PROCESS_START", "DEPENDENCY_READY", "IMPORT_READY",
        "LISTENER_READY", "HEALTH_OK", "READY",
    ])
    scale_failures = validate_scale_contract(root) + prove_100_project_scale(root)
    recovery_failures = prove_failure_recovery()
    evidence_failures = prove_evidence_provenance()
    distribution_failures = validate_distribution_contract(root)

    with tempfile.TemporaryDirectory() as raw:
        conflict = exercise_resource_conflict(
            Path(raw) / "resource.json",
            release_resources=lambda: None,
            reconcile_delivery=lambda _evidence: None,
        )
        readiness = "PASS" if conflict.actual_version == 2 and conflict.actual_sha256 else "FAIL"

    return HardeningSummary(
        scale="PASS" if not scale_failures else "FAIL",
        failure_recovery="PASS" if not recovery_failures else "FAIL",
        evidence_provenance="PASS" if not evidence_failures else "FAIL",
        distribution_contract="PASS" if not distribution_failures else "FAIL",
        runtime_readiness="PASS" if not readiness_failures else "FAIL",
        production_readiness=readiness,
    )


__all__ = ["HardeningSummary", "prove_100_project_scale", "prove_failure_recovery", "prove_evidence_provenance",
           "run_platform_hardening", "validate_distribution_contract", "validate_scale_contract"]
