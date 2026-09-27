import unittest
from tools.platform_repair_engine import plan
class RepairEngineTest(unittest.TestCase):
    def test_missing_is_hold(self): self.assertEqual(plan("missing/path.py","tools/x.py")["status"],"HOLD")
    def test_exact_reference_is_noop(self): self.assertEqual(plan("tools/platform_self_reconciliation.py","tools/x.py")["status"],"NOOP")
if __name__=="__main__": unittest.main()
