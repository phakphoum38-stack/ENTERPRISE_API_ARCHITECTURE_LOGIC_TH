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
    required_fragments = {
        "workflow_dispatch": "orchestrator must support manual dispatch",
        "concurrency:": "orchestrator concurrency guard is missing",
        "cancel-in-progress: false": "orchestrator must not cancel an active run",
        "RECOVERY_STAGE": "recovery stage correlation is missing",
        "RECOVERY_RUN_ID": "recovery run correlation is missing",
        "inputs.ref": "exact ref input is missing",
        "git rev-parse HEAD": "target SHA must be resolved from the checked-out commit",
        'test "$ACTUAL_SHA" = "$TARGET_SHA"': "checked-out SHA identity gate is missing",
        "target_ref=f\"generate-target-{run_id}\"": "immutable target ref is missing",
        "'ref':target_ref": "downstream dispatch must use the immutable target ref",
        "'target_sha':target_sha": "downstream dispatch must propagate TARGET_SHA",
        "head_sha": "downstream run SHA must be checked",
        "SHA_LINEAGE_FAILURE": "SHA lineage failure must be explicit",
    }
    for fragment, message in required_fragments.items():
        assert fragment in text, message

    # The repair target must be derived from the current branch and checked as
    # an actual shell value. Do not accept a comment-only marker as evidence.
    assert 'repair_ref="refs/heads/${branch}"' in text, "repair path must remain branch-isolated"
    assert 'test "$repair_ref" = "refs/heads/${branch}"' in text, "repair path must be verified"
    assert '"ref":"refs/heads/${branch}"' in text, "repair branch creation must use an isolated ref"
    assert '"sha":"${TARGET_SHA}"' in text, "repair branch must start from TARGET_SHA"

    # V3.5 integrity is a SHA-locked stage and requires its generated delay input.
    assert "v3.5-pr-integrity.yml" in text, "V3.5 integrity stage must be handled"
    assert "expected_sha" in text, "V3.5 expected SHA propagation is missing"
    assert "delay_seconds" in text, "V3.5 delay propagation is missing"

    print(
        f"Generate orchestrator validation passed: {len(stages)} stages, "
        f"{len(dispatchable)} dispatchable downstream workflows, exact-SHA lineage enforced."
    )


if __name__ == "__main__":
    main()
