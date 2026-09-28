import unittest
from v3.research_os_v3.review_reconciliation import ReviewReconciler,ReviewReconciliationError
class ReviewReconciliationTests(unittest.TestCase):
 def test_same_target(self): self.assertTrue(ReviewReconciler().reconcile("a",{"target_sha":"a","status":"PASS"},{"target_sha":"a","entries":[]})["reconciled"])
 def test_mismatch(self):
  with self.assertRaises(ReviewReconciliationError): ReviewReconciler().reconcile("a",{"target_sha":"b","status":"PASS"},{"target_sha":"a","entries":[]})
if __name__=="__main__": unittest.main()
