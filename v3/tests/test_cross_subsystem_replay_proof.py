import unittest
from v3.research_os_v3.cross_subsystem_replay_proof import CrossSubsystemReplayProof,ReplayProofError
class ReplayProofTests(unittest.TestCase):
 def test_conserved(self):
  x={"task_id":"t","event_id":"e","delivery_id":"d","idempotency_key":"i"}; r={**x,"replay_id":"r1"}; self.assertTrue(CrossSubsystemReplayProof().verify(x,r)["verified"])
 def test_changed_task_fails(self):
  x={"task_id":"t","event_id":"e","delivery_id":"d","idempotency_key":"i"}; r={**x,"task_id":"t2"}
  with self.assertRaises(ReplayProofError): CrossSubsystemReplayProof().verify(x,r)
if __name__=="__main__": unittest.main()
