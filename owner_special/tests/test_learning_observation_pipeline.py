from __future__ import annotations

import unittest

from owner_special.research_os_friend.self_learning.observation_pipeline import (
    LearningObservation,
    LearningObservationPipeline,
)


class LearningObservationPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = LearningObservationPipeline()

    def observation(self) -> LearningObservation:
        return LearningObservation(
            owner_id="owner-001",
            trigger="research-failure",
            outcome="validated-repair",
            evidence_refs=("EV-001",),
            context=(("project", "demo"),),
        )

    def test_observation_becomes_deterministic_pattern(self) -> None:
        first = self.pipeline.observe(self.observation())
        second = self.pipeline.observe(self.observation())
        self.assertEqual(first, second)
        self.assertEqual(len(first.observation_fingerprint), 64)

    def test_candidate_binds_pattern_fingerprint(self) -> None:
        pattern = self.pipeline.observe(self.observation())
        candidate = self.pipeline.candidate(
            pattern,
            name="bounded-research",
            goal="reuse validated repair",
            procedure=("inspect", "validate"),
            evidence=("EV-001",),
            confidence=0.95,
        )
        self.assertEqual(candidate.metadata["observation_fingerprint"], pattern.observation_fingerprint)

    def test_sandbox_is_deterministic_and_isolated(self) -> None:
        pattern = self.pipeline.observe(self.observation())
        candidate = self.pipeline.candidate(
            pattern,
            name="bounded-research",
            goal="reuse validated repair",
            procedure=("inspect", "validate"),
            evidence=("EV-001",),
            confidence=0.95,
        )
        first = self.pipeline.sandbox(candidate)
        second = self.pipeline.sandbox(candidate)
        self.assertEqual(first, second)
        self.assertTrue(first.isolated)

    def test_invalid_observation_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            self.pipeline.observe(LearningObservation(owner_id="", trigger="x", outcome="y"))


if __name__ == "__main__":
    unittest.main()
