import unittest
from v3.research_os_v3.scenario_algebra import ScenarioAlgebra, ScenarioDimension
from v3.research_os_v3.pairwise_scenario_planner import PairwiseScenarioPlanner

class PairwisePlannerTests(unittest.TestCase):
    def setUp(self):
        self.a=ScenarioAlgebra((ScenarioDimension("workflow",("queued","running","recovered")),ScenarioDimension("lease",("active","expired","reclaimed")),ScenarioDimension("identity",("conserved","duplicate"))))
    def test_dimension_pairs_are_unique(self):
        pairs=PairwiseScenarioPlanner(self.a).dimension_pairs()
        self.assertEqual(3,len(pairs))
        self.assertEqual(3,len({(p.left,p.right) for p in pairs}))
    def test_sampling_uses_boundary_values_and_is_bounded(self):
        rows=PairwiseScenarioPlanner(self.a).pairwise_scenarios(4)
        self.assertEqual(4,len(rows))
        for row in rows:
            self.a.validate(row)
    def test_pairwise_planning_does_not_claim_exhaustive_execution(self):
        planner=PairwiseScenarioPlanner(self.a)
        self.assertLess(len(planner.pairwise_scenarios(2)), self.a.cardinality)

if __name__ == "__main__": unittest.main()