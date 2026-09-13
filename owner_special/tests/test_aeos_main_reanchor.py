"""Negative-first tests for the AEOS main re-anchor boundary."""
from __future__ import annotations

import unittest

from owner_special.research_os_friend.aeos_main_reanchor import (
    ReanchorError,
    create_reanchor_observation,
    reanchor_baseline,
)


OLD = "a" * 40
NEW = "b" * 40


class MainReanchorTests(unittest.TestCase):
    def test_valid_verified_observation_reanchors_to_observed_main(self) -> None:
        observation = create_reanchor_observation(
            mission_id="M1",
            previous_baseline_sha=OLD,
            observed_main_sha=NEW,
            evidence_refs=("EV-MAIN-1",),
        )
        self.assertEqual(reanchor_baseline(observation), NEW)

    def test_stale_or_invalid_sha_is_rejected(self) -> None:
        with self.assertRaises(ReanchorError):
            create_reanchor_observation(
                mission_id="M1",
                previous_baseline_sha=OLD,
                observed_main_sha="not-a-sha",
                evidence_refs=("EV-MAIN-1",),
            )

    def test_unverified_main_cannot_reanchor(self) -> None:
        with self.assertRaises(ReanchorError):
            create_reanchor_observation(
                mission_id="M1",
                previous_baseline_sha=OLD,
                observed_main_sha=NEW,
                evidence_refs=("EV-MAIN-1",),
                main_verified=False,
            )

    def test_duplicate_evidence_is_rejected(self) -> None:
        with self.assertRaises(ReanchorError):
            create_reanchor_observation(
                mission_id="M1",
                previous_baseline_sha=OLD,
                observed_main_sha=NEW,
                evidence_refs=("EV-1", "EV-1"),
            )

    def test_tampered_digest_cannot_be_accepted(self) -> None:
        observation = create_reanchor_observation(
            mission_id="M1",
            previous_baseline_sha=OLD,
            observed_main_sha=NEW,
            evidence_refs=("EV-MAIN-1",),
        )
        with self.assertRaises(ReanchorError):
            type(observation)(
                mission_id=observation.mission_id,
                previous_baseline_sha=observation.previous_baseline_sha,
                observed_main_sha=observation.observed_main_sha,
                evidence_refs=observation.evidence_refs,
                evidence_digest="0" * 64,
                main_verified=True,
            )


if __name__ == "__main__":
    unittest.main()
