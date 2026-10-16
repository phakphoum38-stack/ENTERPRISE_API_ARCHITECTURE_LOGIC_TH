from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REGISTRY = ROOT / "current" / "GENERATE_WORKFLOW_REGISTRY.yml"
ORCHESTRATOR = WORKFLOWS / "generate-orchestrator.yml"
RELEASE = WORKFLOWS / "release.yml"
SUPPORTED_REQUIRED_INPUTS = {"target_sha", "expected_sha", "delay_seconds", "candidate_run_id"}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def workflow_dispatch_inputs(path: Path) -> dict:
    document = load_yaml(path)
    # PyYAML's YAML 1.1 resolver may parse the key "on" as boolean True.
    events = document.get("on") or document.get(True) or {}
    dispatch = events.get("workflow_dispatch") or {}
    return dispatch.get("inputs") or {}


def main() -> None:
    registry = load_yaml(REGISTRY)
    stages = registry.get("stages") or []
    assert stages, "registry stages must not be empty"

    files = {p.name for p in WORKFLOWS.glob("*.y*ml")}
    seen = set()
    ordered = []
    by_file = {}

    for entry in stages:
        assert isinstance(entry, dict), f"invalid stage entry: {entry!r}"
        stage = int(entry["stage"])
        workflow = entry["file"]
        assert stage not in seen, f"duplicate stage: {stage}"
        seen.add(stage)
        assert workflow in files, f"registry references missing workflow: {workflow}"
        assert workflow not in by_file, f"workflow appears more than once in registry: {workflow}"
        by_file[workflow] = entry
        ordered.append((stage, workflow))

        if entry.get("dispatchable") is True:
            path = WORKFLOWS / workflow
            inputs = workflow_dispatch_inputs(path)
            document = load_yaml(path)
            events = document.get("on") or document.get(True) or {}
            assert "workflow_dispatch" in events, f"{workflow} is dispatchable but has no workflow_dispatch trigger"
            unsupported = [
                name for name, spec in inputs.items()
                if isinstance(spec, dict) and spec.get("required") is True
                and name not in SUPPORTED_REQUIRED_INPUTS
            ]
            assert not unsupported, f"{workflow} has required inputs the orchestrator cannot supply: {unsupported}"

    assert ordered == sorted(ordered), "registry stages must be ordered"
    orchestrator_entry = by_file.get(ORCHESTRATOR.name)
    assert orchestrator_entry is not None, "orchestrator must appear exactly once in registry"
    assert orchestrator_entry.get("dispatchable") is False, "orchestrator must never be dispatchable"

    candidate = by_file.get("v3-candidate.yml")
    release = by_file.get("release.yml")
    assert candidate and candidate.get("dispatchable") is True, "V3 candidate must be a registered dispatchable stage"
    assert release and release.get("dispatchable") is True, "release must be a registered dispatchable stage"
    assert int(candidate["stage"]) < int(release["stage"]), "V3 candidate must finish before release is dispatched"

    candidate_inputs = workflow_dispatch_inputs(WORKFLOWS / "v3-candidate.yml")
    release_inputs = workflow_dispatch_inputs(RELEASE)
    assert "target_sha" in candidate_inputs, "V3 candidate must accept target_sha"
    assert {"target_sha", "candidate_run_id"} <= set(release_inputs), "release must accept exact SHA and candidate run ID"

    release_text = RELEASE.read_text(encoding="utf-8")
    assert 'test "$workflow" = "Research OS V3 Candidate"' in release_text, (
        "release must verify the exact V3 candidate workflow that emits its artifact"
    )
    candidate_text = (WORKFLOWS / "v3-candidate.yml").read_text(encoding="utf-8")
    artifact_name = "research-os-v3-verified-candidate-${{ env.TARGET_SHA }}"
    assert artifact_name in candidate_text, "V3 candidate artifact name contract changed"

    text = ORCHESTRATOR.read_text(encoding="utf-8")
    required_fragments = {
        "workflow_dispatch": "orchestrator must support manual dispatch",
        "cancel-in-progress: false": "orchestrator must not cancel an active run",
        "git rev-parse HEAD": "target SHA must be resolved from the checked-out commit",
        'test "$ACTUAL_SHA" = "$TARGET_SHA"': "checked-out SHA identity gate is missing",
        "candidate_run_id": "release must receive the successful V3 candidate run ID",
        "head_sha": "downstream run SHA must be checked",
        "SHA_LINEAGE_FAILURE": "SHA lineage failure must be explicit",
        "head_branch": "downstream run must be correlated to the unique target branch",
        "generate-target-{run_id}-{run_attempt}": "target branch must be unique per run attempt",
        "unsupported required inputs": "orchestrator must reject unsupported required workflow inputs",
    }
    for fragment, message in required_fragments.items():
        assert fragment in text, message

    assert 'test "$repair_ref" = "refs/heads/${branch}"' not in text, (
        "tautological repair-ref validation must not be used"
    )
    assert "existing_sha" in text, "existing repair refs must be checked against TARGET_SHA"
    assert "Upload repair evidence artifact" in text, "repair evidence must persist outside the ephemeral runner"

    print(
        f"Generate orchestrator contract validation passed: {len(stages)} stages, "
        f"{sum(1 for e in stages if e.get('dispatchable') is True)} dispatchable workflows, "
        "V3 candidate-before-release and exact-SHA contracts enforced."
    )


if __name__ == "__main__":
    main()
