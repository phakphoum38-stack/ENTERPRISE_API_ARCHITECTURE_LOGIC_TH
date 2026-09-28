import unittest
from v3.research_os_v3.identity_conservation_aggregator import IdentityConservationAggregator

class IdentityAggregatorTests(unittest.TestCase):
    def setUp(self): self.a=IdentityConservationAggregator()
    def test_conserved_identity(self):
        r=self.a.aggregate([{"task_id":"t1","event_id":"e1","delivery_id":"d1","idempotency_key":"i1"}])
        self.assertTrue(r["conserved"]); self.assertFalse(r["duplicate_logical_identity"])
    def test_duplicate_logical_identity_is_visible(self):
        row={"task_id":"t1","event_id":"e1","delivery_id":"d1","idempotency_key":"i1"}
        r=self.a.aggregate([row,{**row,"delivery_id":"d2"}])
        self.assertTrue(r["duplicate_logical_identity"])
    def test_missing_identity_fails_closed(self):
        with self.assertRaises(ValueError): self.a.aggregate([{"task_id":"t1"}])

if __name__ == "__main__": unittest.main()