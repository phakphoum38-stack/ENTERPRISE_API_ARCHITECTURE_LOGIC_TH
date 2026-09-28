#!/usr/bin/env python3
"""Negative assurance tests for the Owner Authority Packet boundary."""
from __future__ import annotations

import unittest

from tools.aeos_authority_packet import AuthorityPacket, packet_digest


SHA = "a" * 40
EVIDENCE = "b" * 64


def valid_packet(**overrides):
    values = {
        "original_change": "change-1",
        "original_failure": "failure-1",
        "root_cause": "cause-1",
        "root_cause_proof": (EVIDENCE,),
        "fix_attempts": ("attempt-1",),
        "final_fix": "fix-1",
        "failed_controls_history": ("control-1",),
        "resolved_failures": ("failure-1",),
        "new_regressions": (),
        "exact_sha": SHA,
        "provenance": ("source-sha-bound",),
        "evidence_integrity": ("digest-verified",),
        "forensic_result": "PASS",
        "independent_review": "PASS",
        "remaining_risks": (),
        "remaining_assumptions": (),
        "assurance_debt": (),
        "recommended_decision": "APPROVE",
    }
    values.update(overrides)
    return AuthorityPacket(**values)


class AuthorityPacketNegativeAssuranceTests(unittest.TestCase):
    def test_valid_packet_is_accepted(self):
        packet = valid_packet()
        packet.validate()
        self.assertEqual(packet.canonical()["authority_boundary"]["autobot_may_merge"], False)

    def test_missing_root_cause_proof_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "root_cause_proof_missing"):
            valid_packet(root_cause_proof=()).validate()

    def test_invalid_root_cause_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_root_cause_evidence_id"):
            valid_packet(root_cause_proof=("not-evidence",)).validate()

    def test_missing_fix_attempt_history_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "fix_attempt_history_missing"):
            valid_packet(fix_attempts=()).validate()

    def test_missing_provenance_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "provenance_missing"):
            valid_packet(provenance=()).validate()

    def test_missing_evidence_integrity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "evidence_integrity_missing"):
            valid_packet(evidence_integrity=()).validate()

    def test_failed_forensic_result_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "forensic_not_pass"):
            valid_packet(forensic_result="FAIL").validate()

    def test_failed_independent_review_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "independent_review_not_pass"):
            valid_packet(independent_review="HOLD").validate()

    def test_invalid_exact_sha_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_exact_sha"):
            valid_packet(exact_sha="bad").validate()

    def test_invalid_recommended_decision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_recommended_decision"):
            valid_packet(recommended_decision="MERGE").validate()

    def test_packet_digest_is_deterministic(self):
        first = packet_digest(valid_packet())
        second = packet_digest(valid_packet())
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_autobot_cannot_approve_or_merge(self):
        boundary = valid_packet().canonical()["authority_boundary"]
        self.assertTrue(boundary["autobot_may_prepare"])
        self.assertTrue(boundary["autobot_may_recommend"])
        self.assertFalse(boundary["autobot_may_approve"])
        self.assertFalse(boundary["autobot_may_merge"])


if __name__ == "__main__":
    unittest.main()
