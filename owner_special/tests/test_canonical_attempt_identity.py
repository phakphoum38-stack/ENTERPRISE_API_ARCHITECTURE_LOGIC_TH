"""Regression tests for P0-2 canonical attempt identity."""
from __future__ import annotations
import unittest
from owner_special.research_os_friend.canonical_attempt_identity import AttemptIdentityError, assert_same_attempt_lineage, first_attempt
class CanonicalAttemptIdentityTests(unittest.TestCase):
    def test_first_attempt_has_no_retry_parent(self):
        a=first_attempt(mission_id="M1",work_id="W1",task_id="T1",run_id="R1",attempt_id="A1")
        self.assertEqual(a.attempt_number,1); self.assertIsNone(a.retry_of); self.assertFalse(a.is_retry)
    def test_retry_creates_new_identity_with_same_run_lineage(self):
        a=first_attempt(mission_id="M1",work_id="W1",task_id="T1",run_id="R1",attempt_id="A1"); b=a.retry(attempt_id="A2")
        self.assertEqual(b.attempt_number,2); self.assertEqual(b.retry_of,"A1"); assert_same_attempt_lineage(a,b)
    def test_retry_is_not_a_new_task_or_run(self):
        a=first_attempt(mission_id="M1",work_id="W1",task_id="T1",run_id="R1",attempt_id="A1"); b=a.retry(attempt_id="A2")
        self.assertEqual(b.task_id,a.task_id); self.assertEqual(b.run_id,a.run_id)
    def test_retry_parent_must_be_immediate_previous_attempt(self):
        a=first_attempt(mission_id="M1",work_id="W1",task_id="T1",run_id="R1",attempt_id="A1"); b=a.retry(attempt_id="A2"); c=b.retry(attempt_id="A3")
        with self.assertRaisesRegex(AttemptIdentityError,"immediately previous attempt"): assert_same_attempt_lineage(a,c)
    def test_lineage_conflict_fails_closed(self):
        a=first_attempt(mission_id="M1",work_id="W1",task_id="T1",run_id="R1",attempt_id="A1")
        bad=type(a.retry(attempt_id="A2"))(mission_id="M1",work_id="W1",task_id="T2",run_id="R1",attempt_id="A2",attempt_number=2,retry_of="A1")
        with self.assertRaisesRegex(AttemptIdentityError,"task_id attempt lineage conflict"): assert_same_attempt_lineage(a,bad)
    def test_fingerprint_is_deterministic(self):
        a=first_attempt(mission_id="M1",work_id="W1",task_id="T1",run_id="R1",attempt_id="A1"); b=first_attempt(mission_id="M1",work_id="W1",task_id="T1",run_id="R1",attempt_id="A1")
        self.assertEqual(a.fingerprint(),b.fingerprint())
if __name__=="__main__": unittest.main()
