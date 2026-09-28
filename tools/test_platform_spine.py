import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.platform_spine import PlatformSpine
class PlatformSpineTests(unittest.TestCase):
    def setUp(self): self.engine=PlatformSpine()
    def test_full_spine_validates(self): self.assertTrue(self.engine.validate().ok,self.engine.validate().errors)
    def test_dependency_graph_has_no_cycle(self): self.assertEqual(self.engine.detect_cycles(),[])
    def test_forbidden_plane_edges_are_absent(self): self.assertEqual(self.engine.forbidden_plane_edges(),[])
    def test_transitive_impact_is_computed(self):
        impact=self.engine.impact(["platform_graph"]); self.assertEqual(impact["status"],"PASS"); self.assertIn("self_reconciliation",impact["transitive_impact"])
    def test_unknown_impact_holds(self): self.assertEqual(self.engine.impact(["does_not_exist"])["status"],"HOLD")
    def test_lifecycle_is_forward_only(self):
        self.assertTrue(self.engine.validate_lifecycle_transition("ACTIVE","DEPRECATED").ok); self.assertFalse(self.engine.validate_lifecycle_transition("ACTIVE","EXPERIMENTAL").ok)
    def test_required_component_cannot_retire(self): self.assertFalse(self.engine.validate_lifecycle_transition("DEPRECATED","RETIRED",required=True).ok)
    def test_breaking_change_requires_migration(self):
        self.assertFalse(self.engine.validate_compatibility("platform_graph",breaking=True,migration_present=False).ok); self.assertTrue(self.engine.validate_compatibility("platform_graph",breaking=True,migration_present=True).ok)
    def test_health_never_authorizes(self):
        self.assertFalse(self.engine.validate_health("READY",authorization_decision="ALLOW").ok); self.assertTrue(self.engine.validate_health("READY").ok)
    def test_migration_plan(self):
        plan=self.engine.migration_plan("platform_graph","1.0","2.0",breaking=True); self.assertEqual(plan["status"],"REQUIRED"); self.assertTrue(plan["rollback_required"])
    def test_high_impact_simulation_requires_failure_check(self):
        result=self.engine.simulate(["platform_graph"],"CROSS_PROJECT"); self.assertEqual(result["status"],"PASS"); self.assertEqual(result["checks"]["failure"],"REQUIRED_BEFORE_CHANGE")
    def test_cli_validation(self):
        result=subprocess.run([sys.executable,"tools/platform_spine.py","--validate"],cwd=ROOT,text=True,capture_output=True); self.assertEqual(result.returncode,0,result.stdout+result.stderr); self.assertIn("PLATFORM_SPINE=PASS",result.stdout)
if __name__=="__main__": unittest.main()
