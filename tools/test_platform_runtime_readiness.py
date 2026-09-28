import unittest

from tools.platform_runtime_readiness import (
    RuntimeReadiness,
    build_readiness_evidence,
    validate_readiness_sequence,
)


class PlatformRuntimeReadinessTests(unittest.TestCase):
    def test_canonical_sequence_reaches_ready(self) -> None:
        states = [
            "PROCESS_START",
            "DEPENDENCY_READY",
            "IMPORT_READY",
            "LISTENER_READY",
            "HEALTH_OK",
            "READY",
        ]
        self.assertEqual(validate_readiness_sequence(states), ())
        runtime = RuntimeReadiness("a" * 40, "corr-001")
        for state in states[1:]:
            runtime.advance(state)
        runtime.require_ready()

    def test_skipping_health_is_rejected(self) -> None:
        self.assertIn(
            "invalid_transition:LISTENER_READY->READY",
            validate_readiness_sequence(
                ["PROCESS_START", "DEPENDENCY_READY", "IMPORT_READY",
                 "LISTENER_READY", "READY"]
            ),
        )

    def test_unknown_state_is_fail_closed(self) -> None:
        self.assertIn(
            "unknown_state:MAGIC_READY",
            validate_readiness_sequence(
                ["PROCESS_START", "MAGIC_READY", "READY"]
            ),
        )

    def test_evidence_is_a_projection_not_authority(self) -> None:
        evidence = build_readiness_evidence(
            source_sha="b" * 40,
            correlation_id="corr-002",
            states=[
                "PROCESS_START", "DEPENDENCY_READY", "IMPORT_READY",
                "LISTENER_READY", "HEALTH_OK", "READY",
            ],
        )
        self.assertEqual(evidence[-1]["state"], "READY")
        self.assertEqual(evidence[-1]["result"], "PASS")
        self.assertEqual(evidence[-1]["source_sha"], "b" * 40)


if __name__ == "__main__":
    unittest.main()
