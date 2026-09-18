import unittest
from v3.research_os_v3.evidence_ledger import EvidenceLedger,EvidenceLedgerError
class EvidenceLedgerTests(unittest.TestCase):
 def test_append_is_deterministic(self):
  x=EvidenceLedger().append({"target_sha":"a"*40}, {"scenario":"s","passed":True}); self.assertEqual(len(x["ledger_hash"]),64)
 def test_target_required(self):
  with self.assertRaises(EvidenceLedgerError): EvidenceLedger().append({}, {"passed":True})
if __name__=="__main__": unittest.main()
