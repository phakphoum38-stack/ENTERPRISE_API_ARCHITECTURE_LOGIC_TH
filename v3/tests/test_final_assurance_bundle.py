import unittest
from v3.research_os_v3.final_assurance_bundle import FinalAssuranceBundle,FinalAssuranceBundleError
class FinalBundleTests(unittest.TestCase):
 def test_build(self):
  x=FinalAssuranceBundle().build({"target_sha":"a","ledger_hash":"b"},{"target_sha":"a","status":"PASS"},{"target_sha":"a"},{"certified":True}); self.assertEqual(len(x["bundle_hash"]),64)
 def test_review_hold(self):
  with self.assertRaises(FinalAssuranceBundleError): FinalAssuranceBundle().build({"target_sha":"a"},{"target_sha":"a","status":"HOLD"},{"target_sha":"a"},{"certified":True})
if __name__=="__main__": unittest.main()
