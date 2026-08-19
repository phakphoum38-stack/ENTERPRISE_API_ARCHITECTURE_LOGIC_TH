from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "current" / "GENERATE_WORKFLOW_REGISTRY.yml"
INTEGRITY = ROOT / ".github" / "workflows" / "v3.5-pr-integrity.yml"
ORCHESTRATOR = ROOT / ".github" / "workflows" / "generate-orchestrator.yml"
DELAY = ROOT / "v3" / "research_os_v3" / "delay.py"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"{label}: missing {needle!r}"


def main() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")
    integrity = INTEGRITY.read_text(encoding="utf-8")
    orchestrator = ORCHESTRATOR.read_text(encoding="utf-8")
    delay = DELAY.read_text(encoding="utf-8")

    # Registry/order guard: V3.5 integrity must run before release.
    require(registry, "stage: 75", "registry")
    require(registry, "file: v3.5-pr-integrity.yml", "registry")
    require(registry, "role: sha-locked-validation-gate", "registry")
    require(registry, "stage: 80", "registry")
    require(registry, "file: release.yml", "registry")
    assert registry.index("stage: 75") < registry.index("stage: 80"), "V3.5 gate must precede release gate"
    require(registry, "sha_locked_validation_must_precede_release_gate: true", "registry")

    # Orchestrator guard: it must remain non-dispatchable.
    require(orchestrator, "file: generate-orchestrator.yml", "orchestrator")
    require(orchestrator, "dispatchable: false", "orchestrator")

    # Exact-SHA guard must exist and compare the checked-out commit.
    require(integrity, "ref: ${{ steps.target.outputs.target_sha }}", "integrity")
    require(integrity, 'ACTUAL_SHA="$(git rev-parse HEAD)"', "integrity")
    require(integrity, 'test "$ACTUAL_SHA" = "$TARGET_SHA"', "integrity")

    # Delay contract guard: one value is supplied to integrity; no fresh random value there.
    require(integrity, "delay_seconds:", "integrity")
    require(integrity, "inputs.delay_seconds", "integrity")
    assert "random.uniform" not in integrity, "integrity workflow must not generate a second delay"

    # Runtime delay implementation must preserve one immutable value.
    require(delay, "class GeneratedDelay", "delay")
    require(delay, "sleeper(self.seconds)", "delay")
    require(delay, "return self.seconds", "delay")
    require(delay, "if self.seconds < 0", "delay")

    # Scope guard: required worker-pool validation remains present.
    for path in (
        "v3/worker_pool.py",
        "v3/tests/test_worker_pool.py",
        "v3/tests/test_worker_pool_shutdown.py",
        "v3/tests/test_worker_pool_timeout.py",
    ):
        assert (ROOT / path).is_file(), f"missing required V3.5 path: {path}"

    print("V3.5 contract guard: PASS")


if __name__ == "__main__":
    main()
