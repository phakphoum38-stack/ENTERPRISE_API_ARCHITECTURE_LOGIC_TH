from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .factory import SoftwareFactoryPlan
from .models import OrchestrationDecision, Workload

StageHandler = Callable[["FactoryExecutionContext"], Mapping[str, object] | None]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FactoryExecutionContext:
    workload: Workload
    decision: OrchestrationDecision
    plan: SoftwareFactoryPlan
    active_workers: int
    queued_tasks: int
    release_inputs: Mapping[str, object]


@dataclass(frozen=True)
class StageEvidence:
    name: str
    status: str
    output_sha256: str | None = None
    error_type: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": self.name,
            "status": self.status,
        }
        if self.output_sha256 is not None:
            payload["output_sha256"] = self.output_sha256
        if self.error_type is not None:
            payload["error_type"] = self.error_type
        return payload


@dataclass(frozen=True)
class FactoryExecutionResult:
    execution_id: str
    status: str
    input_sha256: str
    active_workers: int
    queued_tasks: int
    logical_capacity: int
    stages: tuple[StageEvidence, ...]
    release_manifest: dict[str, object] | None

    @property
    def passed(self) -> bool:
        return self.status == "passed"


class AtomicExecutionEvidenceStore:
    """Atomic incremental evidence: earlier passed stages survive later failure."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(
        self,
        *,
        execution_id: str,
        input_sha256: str,
        context: FactoryExecutionContext,
    ) -> None:
        payload = {
            "schema_version": 1,
            "contract": "software-factory-execution-v3-clean",
            "execution_id": execution_id,
            "status": "in_progress",
            "input_sha256": input_sha256,
            "profile": context.decision.profile.tier.value,
            "logical_capacity": context.decision.profile.capacity,
            "active_workers": context.active_workers,
            "queued_tasks": context.queued_tasks,
            "release_inputs_sha256": _sha256(dict(context.release_inputs)),
            "stages": {},
        }
        self._write(payload)

    def record(self, evidence: StageEvidence) -> None:
        payload = self._read()
        stages = payload.setdefault("stages", {})
        if not isinstance(stages, dict):
            raise ValueError("execution evidence stages must be an object")
        stages[evidence.name] = evidence.to_dict()
        self._write(payload)

    def finalize(
        self,
        *,
        status: str,
        release_manifest: Mapping[str, object] | None,
    ) -> None:
        payload = self._read()
        payload["status"] = status
        if release_manifest is not None:
            payload["release_manifest"] = dict(release_manifest)
        self._write(payload)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("execution evidence must be a JSON object")
        return payload

    def _write(self, payload: Mapping[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)


class FactoryExecutionEngine:
    """Sequential governed pipeline with bounded active worker allocation."""

    contract = "software-factory-execution-v3-clean"

    def __init__(self, *, hard_concurrency_limit: int = 64) -> None:
        if hard_concurrency_limit < 1:
            raise ValueError("hard_concurrency_limit must be at least 1")
        self.hard_concurrency_limit = hard_concurrency_limit

    def execute(
        self,
        *,
        workload: Workload,
        decision: OrchestrationDecision,
        plan: SoftwareFactoryPlan,
        handlers: Mapping[str, StageHandler],
        release_inputs: Mapping[str, object] | None = None,
        evidence_path: Path | None = None,
    ) -> FactoryExecutionResult:
        release_inputs = dict(release_inputs or {})
        requested_parallelism = max(1, workload.parallelism)
        active_workers = min(
            decision.demand,
            decision.profile.capacity,
            requested_parallelism,
            self.hard_concurrency_limit,
        )
        queued_tasks = max(0, decision.demand - active_workers)

        input_payload = {
            "contract": self.contract,
            "workload": {
                "estimated_leaf_tasks": workload.estimated_leaf_tasks,
                "risk": workload.risk,
                "parallelism": workload.parallelism,
            },
            "decision": {
                "profile": decision.profile.tier.value,
                "fanout": decision.profile.fanout,
                "depth": decision.profile.depth,
                "logical_capacity": decision.profile.capacity,
                "provider": decision.provider,
                "demand": decision.demand,
            },
            "plan": [stage.name for stage in plan.stages],
            "hard_concurrency_limit": self.hard_concurrency_limit,
            "release_inputs_sha256": _sha256(release_inputs),
        }
        input_sha256 = _sha256(input_payload)
        execution_id = f"v3exec-{input_sha256[:20]}"
        context = FactoryExecutionContext(
            workload=workload,
            decision=decision,
            plan=plan,
            active_workers=active_workers,
            queued_tasks=queued_tasks,
            release_inputs=release_inputs,
        )

        store = AtomicExecutionEvidenceStore(evidence_path) if evidence_path else None
        if store is not None:
            store.initialize(
                execution_id=execution_id,
                input_sha256=input_sha256,
                context=context,
            )

        collected: list[StageEvidence] = []
        for stage in plan.stages:
            handler = handlers.get(stage.name)
            if handler is None:
                failed = StageEvidence(
                    name=stage.name,
                    status="failed",
                    error_type="MissingStageHandler",
                )
                collected.append(failed)
                if store is not None:
                    store.record(failed)
                    store.finalize(status="failed", release_manifest=None)
                return self._failed_result(
                    execution_id=execution_id,
                    input_sha256=input_sha256,
                    context=context,
                    stages=collected,
                )

            try:
                output = dict(handler(context) or {})
                output_sha256 = _sha256(output)
            except Exception as exc:  # stage boundary deliberately converts to evidence
                failed = StageEvidence(
                    name=stage.name,
                    status="failed",
                    error_type=type(exc).__name__,
                )
                collected.append(failed)
                if store is not None:
                    store.record(failed)
                    store.finalize(status="failed", release_manifest=None)
                return self._failed_result(
                    execution_id=execution_id,
                    input_sha256=input_sha256,
                    context=context,
                    stages=collected,
                )

            passed = StageEvidence(
                name=stage.name,
                status="passed",
                output_sha256=output_sha256,
            )
            collected.append(passed)
            if store is not None:
                store.record(passed)

        manifest_core = {
            "schema_version": 1,
            "contract": self.contract,
            "execution_id": execution_id,
            "input_sha256": input_sha256,
            "profile": decision.profile.tier.value,
            "logical_capacity": decision.profile.capacity,
            "active_workers": active_workers,
            "queued_tasks": queued_tasks,
            "provider": decision.provider,
            "release_inputs_sha256": _sha256(release_inputs),
            "stage_output_sha256": {
                stage.name: stage.output_sha256 for stage in collected
            },
        }
        release_manifest = {
            **manifest_core,
            "release_sha256": _sha256(manifest_core),
        }
        if store is not None:
            store.finalize(status="passed", release_manifest=release_manifest)

        return FactoryExecutionResult(
            execution_id=execution_id,
            status="passed",
            input_sha256=input_sha256,
            active_workers=active_workers,
            queued_tasks=queued_tasks,
            logical_capacity=decision.profile.capacity,
            stages=tuple(collected),
            release_manifest=release_manifest,
        )

    @staticmethod
    def _failed_result(
        *,
        execution_id: str,
        input_sha256: str,
        context: FactoryExecutionContext,
        stages: list[StageEvidence],
    ) -> FactoryExecutionResult:
        return FactoryExecutionResult(
            execution_id=execution_id,
            status="failed",
            input_sha256=input_sha256,
            active_workers=context.active_workers,
            queued_tasks=context.queued_tasks,
            logical_capacity=context.decision.profile.capacity,
            stages=tuple(stages),
            release_manifest=None,
        )
