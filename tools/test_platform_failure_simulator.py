import unittest
from platform_failure_simulator import simulate
class FailureSimulatorTest(unittest.TestCase):
    def test_resource_conflict_releases(self): self.assertEqual(simulate("resource_conflict")["expected_action"],"REJECT_AND_RELEASE")
    def test_stale_delivery_rejects(self): self.assertEqual(simulate("stale_delivery")["expected_action"],"REJECT")
    def test_unknown_holds(self): self.assertEqual(simulate("unknown")["status"],"HOLD")
if __name__=="__main__": unittest.main()
