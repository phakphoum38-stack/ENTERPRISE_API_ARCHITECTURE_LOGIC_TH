import unittest
from v3.research_os_v3.runtime_evidence_reconciliation import RuntimeEvidenceReconciler
class ReconciliationTests(unittest.TestCase):
 def test_reconciled(self): self.assertTrue(RuntimeEvidenceReconciler().reconcile([{"target_sha":"a","passed":True,"evidence_hash":"b"}],"a")["reconciled"])
 def test_mismatch_fails_closed(self): self.assertFalse(RuntimeEvidenceReconciler().reconcile([{"target_sha":"b","passed":True,"evidence_hash":"c"}],"a")["reconciled"])
if __name__=="__main__": unittest.main()
