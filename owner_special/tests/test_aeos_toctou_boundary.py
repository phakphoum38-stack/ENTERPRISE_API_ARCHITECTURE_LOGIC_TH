import hashlib
import json
import unittest

from owner_special.research_os_friend.aeos_toctou_boundary import (
    TOCTOUError,
    bind_observation_for_mutation,
)


BASE = "a" * 40
LEASE = "lease-1"
REFS = ("EV-001", "EV-002")


def digest(observed=BASE, lease=LEASE, refs=REFS):
    payload = {
        "work_id": "W-001",
        "baseline_sha": BASE,
        "observed_sha": observed,
        "lease_id": lease,
        "evidence_refs": list(refs),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class AEOSTOCTOUTests(unittest.TestCase):
    def test_valid_observation_can_be_rebound(self):
        binding = bind_observation_for_mutation(
            work_id="W-001", baseline_sha=BASE, observed_sha=BASE,
            lease_id=LEASE, evidence_refs=REFS, evidence_digest=digest(),
            current_sha=BASE, current_lease_id=LEASE,
        )
        self.assertTrue(binding.rebound)

    def test_changed_current_sha_is_rejected(self):
        with self.assertRaises(TOCTOUError):
            bind_observation_for_mutation(
                work_id="W-001", baseline_sha=BASE, observed_sha=BASE,
                lease_id=LEASE, evidence_refs=REFS, evidence_digest=digest(),
                current_sha="b" * 40, current_lease_id=LEASE,
            )

    def test_changed_lease_is_rejected(self):
        with self.assertRaises(TOCTOUError):
            bind_observation_for_mutation(
                work_id="W-001", baseline_sha=BASE, observed_sha=BASE,
                lease_id=LEASE, evidence_refs=REFS, evidence_digest=digest(),
                current_sha=BASE, current_lease_id="lease-2",
            )

    def test_tampered_evidence_digest_is_rejected(self):
        with self.assertRaises(TOCTOUError):
            bind_observation_for_mutation(
                work_id="W-001", baseline_sha=BASE, observed_sha=BASE,
                lease_id=LEASE, evidence_refs=REFS, evidence_digest="0" * 64,
                current_sha=BASE, current_lease_id=LEASE,
            )

    def test_observed_sha_must_equal_baseline(self):
        with self.assertRaises(TOCTOUError):
            bind_observation_for_mutation(
                work_id="W-001", baseline_sha=BASE, observed_sha="b" * 40,
                lease_id=LEASE, evidence_refs=REFS, evidence_digest=digest("b" * 40),
                current_sha=BASE, current_lease_id=LEASE,
            )


if __name__ == "__main__":
    unittest.main()
