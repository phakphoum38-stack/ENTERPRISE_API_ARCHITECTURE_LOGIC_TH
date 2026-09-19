import json,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"current"/"EXPERIENCE_GUI_UX_UI_CONTRACT.json"
s=importlib.util.spec_from_file_location("v",ROOT/"tools"/"validate_experience_gui_ux_ui.py"); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m)
class ExperienceContractTests(unittest.TestCase):
 def setUp(self): self.d=json.loads(CONTRACT.read_text())
 def test_identity_is_explicit(self): self.assertEqual(set(self.d["identity"]["required"]),{"product_id","surface_id","screen_id","component_id","implementation_target"})
 def test_workflow_ownership_is_separate(self): self.assertEqual(set(self.d["workflow_ownership"]),{"gui","ux","ui","design_system","visual_regression","accessibility","release"})
 def test_ambiguous_target_holds(self):
  for k in ("missing_identity","ambiguous_identity","unknown_target"): self.assertEqual(self.d["target_resolution"][k],"HOLD")
 def test_ui_cannot_gain_authority(self):
  for k in ("may_mutate_runtime_authority","may_grant_permissions","may_approve_reviews","may_merge","may_enable_auto_merge","may_rewrite_history"): self.assertFalse(self.d["authority"][k])
 def test_evidence_is_not_authority(self): self.assertFalse(self.d["evidence"]["evidence_is_authority"])
 def test_bounded_coverage(self): self.assertEqual(self.d["mathematical_root"]["symbol"],"10^1000"); self.assertEqual(self.d["mathematical_root"]["materialization"],"forbidden")
 def test_validator_passes(self): ok,f,fp=m.validate(CONTRACT); self.assertTrue(ok,f); self.assertEqual(len(fp),64)
