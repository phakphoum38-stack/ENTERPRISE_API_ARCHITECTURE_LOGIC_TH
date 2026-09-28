import unittest
from v3.research_os_v3.replay_certification import ReplayCertification,ReplayCertificationError
class ReplayCertificationTests(unittest.TestCase):
 def test_certify(self):
  x={"task_id":"t","event_id":"e","delivery_id":"d","idempotency_key":"i"}; self.assertTrue(ReplayCertification().certify(x,{**x,"passed":True})["certified"])
 def test_failure(self):
  x={"task_id":"t","event_id":"e","delivery_id":"d","idempotency_key":"i"}
  with self.assertRaises(ReplayCertificationError): ReplayCertification().certify(x,{**x,"passed":False})
if __name__=="__main__": unittest.main()
