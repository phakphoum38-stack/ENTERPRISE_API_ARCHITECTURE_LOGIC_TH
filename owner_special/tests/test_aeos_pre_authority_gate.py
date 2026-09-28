import unittest
from tools.aeos_pre_authority_gate import AuthorityPacket, packet_digest

SHA = "a" * 40
EVIDENCE = "b" * 64
WAVES = tuple(f"W{i}" for i in range(8))


def packet(**overrides):
    data = dict(
        gate_id="gate-1", iteration_id="iter-1", source_sha=SHA,
        required_waves=WAVES,
        wave_results=tuple((w, "PASS") for w in WAVES),
        holds=(), evidence_ids=(EVIDENCE,),
        provenance_verified=True, evidence_integrity_verified=True,
        scope_verified=True, root_cause_verified=True,
        independent_review_verified=True, assurance_self_check_verified=True,
        remaining_risks=(), remaining_assumptions=(), assurance_debt=(),
    )
    data.update(overrides)
    return AuthorityPacket(**data)


class PreAuthorityGateTests(unittest.TestCase):
    def test_ready_requires_all_conditions(self):
        self.assertEqual(packet().decision(), "READY_FOR_AUTHORITY")

    def test_missing_wave_is_hold(self):
        self.assertEqual(packet(wave_results=(("W0", "PASS"),)).decision(), "HOLD")

    def test_failed_wave_is_hold(self):
        results = tuple((w, "FAIL" if w == "W3" else "PASS") for w in WAVES)
        self.assertEqual(packet(wave_results=results).decision(), "HOLD")

    def test_open_hold_is_hold(self):
        self.assertEqual(packet(holds=("hold-1",)).decision(), "HOLD")

    def test_unverified_provenance_is_blocked(self):
        self.assertEqual(packet(provenance_verified=False).decision(), "BLOCKED")

    def test_unverified_review_is_blocked(self):
        self.assertEqual(packet(independent_review_verified=False).decision(), "BLOCKED")

    def test_invalid_sha_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_source_sha"):
            packet(source_sha="bad").decision()

    def test_invalid_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_evidence_id"):
            packet(evidence_ids=("bad",)).decision()

    def test_digest_is_deterministic(self):
        self.assertEqual(packet_digest(packet()), packet_digest(packet()))

    def test_no_owner_or_merge_authority(self):
        decision = packet().decision()
        self.assertNotIn("OWNER_APPROVED", decision)
        self.assertNotIn("MERGED", decision)


if __name__ == "__main__":
    unittest.main(verbosity=2)
