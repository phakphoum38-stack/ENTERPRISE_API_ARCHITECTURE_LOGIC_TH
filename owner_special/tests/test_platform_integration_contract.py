import json,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"current"/"PLATFORM_INTEGRATION_CONTRACT.json"
s=importlib.util.spec_from_file_location("v",ROOT/"tools"/"validate_platform_integration.py"); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m)
class PlatformIntegrationContractTests(unittest.TestCase):
 def setUp(self): self.d=json.loads(CONTRACT.read_text())
 def test_four_planes(self): self.assertEqual(set(self.d["planes"]),{"CORE","ASSURANCE","PLATFORM","EXPERIENCE"})
 def test_no_platform_authority_escalation(self):
  self.assertTrue(self.d["authority"]["platform_may_compose"])
  for k in ("platform_may_mutate_core_authority","platform_may_grant_permissions","platform_may_approve_reviews","platform_may_merge","platform_may_enable_auto_merge","platform_may_rewrite_history"): self.assertFalse(self.d["authority"][k])
 def test_duplicate_subsystems_forbidden(self):
  for x in ("assurance_engine","resource_control_plane","memory_store"): self.assertIn(x,self.d["forbidden_duplicate_subsystems"])
 def test_fail_closed(self): self.assertEqual(self.d["evidence_contract"]["unknown_state"],"HOLD"); self.assertEqual(self.d["evidence_contract"]["conflict_state"],"HOLD")
 def test_bounded_10e1000(self): self.assertEqual(self.d["mathematical_root"]["symbol"],"10^1000"); self.assertEqual(self.d["mathematical_root"]["materialization"],"forbidden"); self.assertEqual(self.d["mathematical_root"]["execution"],"bounded")
 def test_validator(self): ok,f,fp=m.validate(CONTRACT); self.assertTrue(ok,f); self.assertEqual(len(fp),64)
 def test_deterministic(self): self.assertEqual(m.validate(CONTRACT)[2],m.validate(CONTRACT)[2])
