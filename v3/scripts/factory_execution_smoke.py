from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import UnifiedMasterOrchestrator, Workload


def main() -> int:
    master = UnifiedMasterOrchestrator()
    calls: list[str] = []

    def stage(name: str):
        def run(context):
            calls.append(name)
            if name == "team":
                return {
                    "active_workers": context.active_workers,
                    "queued_tasks": context.queued_tasks,
                }
            if name == "tests":
                return {"passed": True, "suite": "v3-clean"}
            if name == "release":
                return {"artifact": "research-os-v3-candidate"}
            return {"stage": name}

        return run

    stage_handlers = {
        name: stage(name)
        for name in ("master", "factory", "team", "tests", "release")
    }

    with tempfile.TemporaryDirectory(prefix="research-os-v3-factory-") as temporary:
        evidence_path = Path(temporary) / "factory-execution.json"
        workload = Workload(
            estimated_leaf_tasks=217,
            risk=1,
            parallelism=1000,
        )
        result = master.execute_factory(
            workload,
            handlers=stage_handlers,
            hard_concurrency_limit=64,
            evidence_path=evidence_path,
            release_inputs={
                "source_sha": "factory-smoke-source",
                "build_policy": "single-governed-pipeline",
            },
        )

        assert result.passed
        assert result.logical_capacity == 46656
        assert result.active_workers == 64
        assert result.active_workers < result.logical_capacity
        assert result.queued_tasks > 0
        assert calls == ["master", "factory", "team", "tests", "release"]
        assert result.release_manifest is not None
        assert len(result.release_manifest["release_sha256"]) == 64

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        assert evidence["status"] == "passed"
        assert list(evidence["stages"]) == calls
        assert evidence["release_manifest"]["release_sha256"] == result.release_manifest["release_sha256"]

        print(
            json.dumps(
                {
                    "status": result.status,
                    "execution_id": result.execution_id,
                    "scale": result.release_manifest["profile"],
                    "logical_capacity": result.logical_capacity,
                    "active_workers": result.active_workers,
                    "queued_tasks": result.queued_tasks,
                    "stages": calls,
                    "release_sha256": result.release_manifest["release_sha256"],
                    "incremental_evidence": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
