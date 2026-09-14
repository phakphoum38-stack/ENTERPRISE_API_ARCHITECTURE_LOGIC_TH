from __future__ import annotations

import unittest

from tools.rebaseline_engine import RebaselineInput, prepare_rebaseline, record_digest


PARENT = "565ab068d5a1540ea799b594ff031ba003e068af"
SUCCESSOR = "897e07a9960b3310b44fa5b359f5e144e4ec2ea8"
EVIDENCE = "a" * 64
PROVENANCE = "b" * 64


def valid_input(**overrides: object) -> RebaselineInput:
    values: dict[str, object] = {
        "parent_sha": PARENT,
        "successor_sha": SUCCESSOR,
        "evidence_root": EVIDENCE,
        "provenance_root": PROVENANCE,
        "assurance_state": "VERIFIED",
        "known_risks": ("example-risk",),
        "lessons_learned": ("example-lesson",),
        "immutability_verified": True,
        "verification_complete": True,
    }
    values.update(overrides)
    return RebaselineInput(**values)


class RebaselineEngineTests(unittest.TestCase):
    def test_valid_successor_records_explicit_lineage(self) -> None:
        record = prepare_rebaseline(valid_input())
        self.assertEqual(record.parent_sha, PARENT)
        self.assertEqual(record.successor_sha, SUCCESSOR)
        self.assertEqual(record.canonical()["state"], "REBASELINE_RECORDED")
        self.assertTrue(record.canonical()["history_policy"]["parent_is_immutable"])
        self.assertTrue(record.canonical()["history_policy"]["certification_is_not_inherited"])
        self.assertEqual(len(record_digest(record)), 64)

    def test_same_sha_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "successor_must_differ_from_parent"):
            prepare_rebaseline(valid_input(successor_sha=PARENT))

    def test_missing_immutability_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "parent_immutability_not_verified"):
            prepare_rebaseline(valid_input(immutability_verified=False))

    def test_incomplete_verification_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "successor_verification_incomplete"):
            prepare_rebaseline(valid_input(verification_complete=False))

    def test_unverified_state_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "successor_not_verified"):
            prepare_rebaseline(valid_input(assurance_state="OBSERVED"))

    def test_invalid_evidence_root_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid_evidence_root"):
            prepare_rebaseline(valid_input(evidence_root="not-a-digest"))


if __name__ == "__main__":
    unittest.main()
