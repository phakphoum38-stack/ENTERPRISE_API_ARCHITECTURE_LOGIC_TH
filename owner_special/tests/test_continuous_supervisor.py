"""Regression tests for P0-7 supervisor decision boundary."""
import unittest
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.canonical_attempt_identity import CanonicalAttempt
from owner_special.research_os_friend.continuous_supervisor import decide, observe, next_attempt
class ContinuousSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.i=CanonicalIdentity("M1","W1","a"*40,task_id="T1",run_id="R1",attempt_id="A1")
        self.a=CanonicalAttempt("M1","W1","T1","R1","A1",1)
    def test_schedule(self):
        self.assertEqual(decide(observe(identity=self.i,state="READY",dependencies_ready=True)).action,"SCHEDULE")
    def test_conflict_quarantines(self):
        self.assertEqual(decide(observe(identity=self.i,state="RUNNING",dependencies_ready=False,conflict_detected=True)).action,"QUARANTINE")
    def test_retry_requires_new_attempt(self):
        d=decide(observe(identity=self.i,state="FAILED",dependencies_ready=False))
        self.assertEqual(d.action,"RETRY"); self.assertTrue(d.requires_new_attempt)
    def test_next_attempt_preserves_lineage(self):
        n=next_attempt(identity=self.i,attempt=self.a)
        self.assertEqual((n.mission_id,n.work_id,n.task_id,n.run_id),("M1","W1","T1","R1"))
        self.assertNotEqual(n.attempt_id,self.a.attempt_id)
if __name__=="__main__": unittest.main()
