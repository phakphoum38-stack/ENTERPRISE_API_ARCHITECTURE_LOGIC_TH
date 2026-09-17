"""Regression tests for P0-5 forensic evidence binding."""
from __future__ import annotations
import unittest
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.forensic_evidence_binding import ForensicEvidenceError, assert_evidence_lineage, bind_forensic_evidence
SHA="a"*40
class ForensicEvidenceBindingTests(unittest.TestCase):
    def setUp(self): self.identity=CanonicalIdentity("M1","W1",SHA)
    def test_binds_forensic_evidence_to_identity(self):
        e=bind_forensic_evidence(identity=self.identity,failure_fingerprint="b"*64,forensic_fingerprint="c"*64,evidence_type="FORENSIC_RESULT",source_refs=("plan:1","probe:1"),evidence_id="EV-001")
        assert_evidence_lineage(e,self.identity); self.assertEqual(e.mission_id,"M1"); self.assertEqual(e.work_id,"W1"); self.assertEqual(e.baseline_sha,SHA); self.assertEqual(len(e.provenance_hash),64)
    def test_lineage_mismatch_fails_closed(self):
        e=bind_forensic_evidence(identity=self.identity,failure_fingerprint="b"*64,forensic_fingerprint="c"*64,evidence_type="FORENSIC_RESULT",source_refs=("probe:1",),evidence_id="EV-001")
        with self.assertRaises(ForensicEvidenceError): assert_evidence_lineage(e,CanonicalIdentity("M1","W2",SHA))
    def test_unknown_hash_shape_fails_closed(self):
        with self.assertRaises(ForensicEvidenceError): bind_forensic_evidence(identity=self.identity,failure_fingerprint="bad",forensic_fingerprint="c"*64,evidence_type="FORENSIC_RESULT",source_refs=("probe:1",),evidence_id="EV-001")
    def test_independence_is_explicit(self):
        e=bind_forensic_evidence(identity=self.identity,failure_fingerprint="b"*64,forensic_fingerprint="c"*64,evidence_type="FORENSIC_RESULT",source_refs=("probe:1",),evidence_id="EV-001",independent=True); self.assertTrue(e.independent)
if __name__=="__main__": unittest.main()
