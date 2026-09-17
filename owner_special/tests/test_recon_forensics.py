import unittest
from dataclasses import dataclass
from enum import Enum

from owner_special.research_os_friend.recon_forensics import (
    ProbeFamily,
    build_forensic_plan,
)

SOURCE = "565ab068d5a1540ea799b594ff031ba003e068af"
TARGET = "759c641b98534434a16eb96aa3dfe4ad224c18bd"
FINGERPRINT = "0" * 64


class Kind(str, Enum):
    CODE_DEFECT = "CODE_DEFECT"
    TRANSIENT = "TRANSIENT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Failure:
    source_sha: str
    failure_fingerprint: str
    kind: Kind


class ReconForensicsAdapterTests(unittest.TestCase):
    def failure(self, kind=Kind.UNKNOWN):
        return Failure(SOURCE, FINGERPRINT, kind)

    def test_unknown_failure_gets_full_bounded_plan(self):
        plan = build_forensic_plan(self.failure(), target_sha=TARGET)
        self.assertEqual(plan.kind, "UNKNOWN")
        self.assertEqual(
            plan.probes,
            (ProbeFamily.DIRECT, ProbeFamily.SHELL, ProbeFamily.PLATFORM),
        )
        self.assertEqual(plan.worker_matrix, (1, 4, 16))
        self.assertFalse(plan.auto_execute)

    def test_code_defect_does_not_claim_platform_concurrency(self):
        plan = build_forensic_plan(self.failure(Kind.CODE_DEFECT), target_sha=TARGET)
        self.assertEqual(plan.kind, "CODE_DEFECT")
        self.assertEqual(plan.probes, (ProbeFamily.DIRECT, ProbeFamily.SHELL))
        self.assertFalse(plan.auto_execute)

    def test_transient_includes_platform_probe(self):
        plan = build_forensic_plan(self.failure(Kind.TRANSIENT), target_sha=TARGET)
        self.assertEqual(plan.kind, "TRANSIENT")
        self.assertEqual(plan.probes, (ProbeFamily.DIRECT, ProbeFamily.PLATFORM))

    def test_integrity_failure_remains_distinct(self):
        plan = build_forensic_plan(self.failure(Kind.INTEGRITY_FAILURE), target_sha=TARGET)
        self.assertEqual(plan.kind, "INTEGRITY_FAILURE")
        self.assertEqual(plan.probes, (ProbeFamily.DIRECT,))
        self.assertFalse(plan.auto_execute)

    def test_worker_matrix_rejects_unbounded_values(self):
        with self.assertRaises(ValueError):
            build_forensic_plan(self.failure(), target_sha=TARGET, worker_values=(1, 32), maximum_workers=16)

    def test_plan_preserves_identity(self):
        plan = build_forensic_plan(self.failure(), target_sha=TARGET)
        self.assertEqual(plan.target_sha, TARGET)
        self.assertEqual(plan.source_sha, SOURCE)
        self.assertEqual(plan.failure_fingerprint, FINGERPRINT)

    def test_rejects_bad_target_sha(self):
        with self.assertRaises(ValueError):
            build_forensic_plan(self.failure(), target_sha="bad")

    def test_rejects_bad_fingerprint(self):
        failure = Failure(SOURCE, "bad", Kind.UNKNOWN)
        with self.assertRaises(ValueError):
            build_forensic_plan(failure, target_sha=TARGET)


if __name__ == "__main__":
    unittest.main()
