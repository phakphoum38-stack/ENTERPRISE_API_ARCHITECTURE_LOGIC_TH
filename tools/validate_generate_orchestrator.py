from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "current" / "GENERATE_WORKFLOW_REGISTRY.yml"
ORCHESTRATOR = ROOT / ".github" / "workflows" / "generate-orchestrator.yml"


def main() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    stages = registry.get("stages") or []
    assert stages, "registry stages must not be empty"

    files = {p.name for p in (ROOT / ".github" / "workflows").glob("*.y*ml")}
    seen = set()
    dispatchable = []

    for entry in stages:
        assert isinstance(entry, dict), f"invalid stage entry: {entry!r}"
        stage = int(entry["stage"])
        workflow = entry["file"]
        assert stage not in seen, f"duplicate stage: {stage}"
        seen.add(stage)
        assert workflow in files, f"registry references missing workflow: {workflow}"
        if entry.get("dispatchable"):
            dispatchable.append((stage, workflow))

    orchestrator_entries = [e for e in stages if e.get("file") == ORCHESTRATOR.name]
    assert len(orchestrator_entries) == 1, "orchestrator must appear exactly once in registry"
    assert orchestrator_entries[0].get("dispatchable") is False, "orchestrator must never be dispatchable"
    assert all(workflow != ORCHESTRATOR.name for _, workflow in dispatchable), "self-dispatch detected"
    assert dispatchable == sorted(dispatchable), "dispatchable stages must be ordered"

    text = ORCHESTRATOR.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text, "orchestrator must support manual dispatch"
    assert "concurrency:" in text, "orchestrator concurrency guard is missing"
    assert "cancel-in-progress: false" in text, "orchestrator must not cancel an active run"
    assert "RECOVERY_STAGE" in text and "RECOVERY_RUN_ID" in text, "recovery correlation is missing"
    assert "refs/heads/${branch}" in text, "repair path must remain branch-isolated"

    print(f"Generate orchestrator validation passed: {len(stages)} stages, {len(dispatchable)} dispatchable downstream workflows.")


if __name__ == "__main__":
    main()
