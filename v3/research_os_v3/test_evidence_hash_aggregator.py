import unittest
from v3.research_os_v3.evidence_hash_aggregator import EvidenceHashAggregator

class EvidenceHashAggregatorTests(unittest.TestCase):
    def test_hash_is_deterministic(self):
        a=EvidenceHashAggregator(); e={"scenario":"x","passed":True,"target_sha":"a"*40}
        self.assertEqual(a.hash_entry(e),a.hash_entry(dict(reversed(list(e.items())))))
    def test_aggregate_is_stable(self):
        a=EvidenceHashAggregator(); rows=[{"scenario":"x","passed":True},{"scenario":"y","passed":False}]
        self.assertEqual(a.aggregate(rows),a.aggregate(rows))
    def test_hash_is_sha256(self): self.assertEqual(64,len(EvidenceHashAggregator().hash_entry({"x":1})))

if __name__ == "__main__": unittest.main()