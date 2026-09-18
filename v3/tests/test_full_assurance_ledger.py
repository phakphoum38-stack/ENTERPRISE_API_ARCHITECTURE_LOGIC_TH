import unittest
from v3.research_os_v3.full_assurance_ledger import AssuranceLedger
class LedgerTests(unittest.TestCase):
 def test_pass(self): self.assertEqual("PASS",AssuranceLedger().build("a",[{"passed":True}])["status"])
 def test_hold(self): self.assertEqual("HOLD",AssuranceLedger().build("a",[{"passed":False}])["status"])
if __name__=="__main__": unittest.main()
