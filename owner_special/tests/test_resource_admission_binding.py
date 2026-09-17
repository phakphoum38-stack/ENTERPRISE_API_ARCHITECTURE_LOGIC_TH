"""Regression tests for P0-6 resource/admission binding."""
from __future__ import annotations
import unittest
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.resource_admission_binding import ResourceAdmissionBindingError, assert_admission_lineage, bind_resource_admission

class ResourceAdmissionBindingTests(unittest.TestCase):
    def setUp(self):
        self.identity=CanonicalIdentity("M1","W1","a"*40,task_id="T1",run_id="R1",attempt_id="A1")
    def test_binding_is_deterministic(self):
        a=bind_resource_admission(identity=self.identity,request_id="REQ-1",admission_id="ADM-1",principal_id="owner",provider="mock",model="m1")
        b=bind_resource_admission(identity=self.identity,request_id="REQ-1",admission_id="ADM-1",principal_id="owner",provider="mock",model="m1")
        assert_admission_lineage(a,self.identity)
        self.assertEqual(a.binding_hash,b.binding_hash)
        self.assertEqual(len(a.binding_hash),64)
    def test_mismatch_fails_closed(self):
        a=bind_resource_admission(identity=self.identity,request_id="REQ-1",admission_id="ADM-1",principal_id="owner")
        other=CanonicalIdentity("M1","W1","a"*40,task_id="T1",run_id="R2",attempt_id="A2")
        with self.assertRaises(ResourceAdmissionBindingError):
            assert_admission_lineage(a,other)
    def test_missing_request_fails_closed(self):
        with self.assertRaises(ResourceAdmissionBindingError):
            bind_resource_admission(identity=self.identity,request_id="",admission_id="ADM-1",principal_id="owner")

if __name__=="__main__":
    unittest.main()
