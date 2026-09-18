from __future__ import annotations
import unittest
from v3.research_os_v3.scenario_algebra import ScenarioAlgebra, ScenarioAlgebraError, ScenarioDimension

class ScenarioAlgebraTests(unittest.TestCase):
    def setUp(self):
        self.a=ScenarioAlgebra((ScenarioDimension("workflow",("queued","running","recovered")),ScenarioDimension("lease",("active","expired","reclaimed")),ScenarioDimension("identity",("conserved","duplicate")),ScenarioDimension("evidence",("observed","target-bound"))))
    def test_cardinality(self): self.assertEqual(36,self.a.cardinality)
    def test_id_deterministic(self):
        s={"evidence":"target-bound","identity":"conserved","lease":"reclaimed","workflow":"recovered"}
        self.assertEqual(self.a.scenario_id(s),self.a.scenario_id(dict(reversed(list(s.items())))))
    def test_sample_bounded(self): self.assertEqual(5,len(self.a.sample(5)))
    def test_missing_fails_closed(self):
        with self.assertRaises(ScenarioAlgebraError): self.a.validate({"workflow":"queued"})
    def test_invalid_value_fails_closed(self):
        with self.assertRaises(ScenarioAlgebraError): self.a.validate({"workflow":"queued","lease":"bad","identity":"conserved","evidence":"observed"})

if __name__ == "__main__": unittest.main()
