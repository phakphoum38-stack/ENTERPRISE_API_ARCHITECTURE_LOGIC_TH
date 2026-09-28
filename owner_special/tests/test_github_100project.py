import json, unittest
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("v",ROOT/"tools"/"validate_github_100project.py")
v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)

class GitHub100ProjectContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads((ROOT/"current"/"GITHUB_100PROJECT_CONTINUOUS_ASSURANCE_CONTRACT.json").read_text(encoding="utf-8"))
    def test_exactly_100_surfaces(self): self.assertEqual(len(self.doc["surfaces"]),100)
    def test_contiguous_ids(self): self.assertEqual([x[0] for x in self.doc["surfaces"]],[f"P{i:02d}" for i in range(1,101)])
    def test_fail_closed(self): self.assertTrue(self.doc["fail_closed"]); self.assertEqual(self.doc["unknown_policy"],"HOLD")
    def test_merge_authority_is_unchanged(self): self.assertEqual(self.doc["merge_authority"],"RECON_OWNER_AUTHORITY_UNCHANGED")
    def test_forbidden_authority_mutations(self):
        f=set(self.doc["mutation_boundary"]["forbidden"])
        self.assertTrue({"merge_pull_requests","enable_auto_merge","grant_permissions","change_branch_protection"}<=f)
    def test_validator_passes(self): self.assertEqual(v.validate(self.doc),[])
    def test_deterministic_fingerprint(self): self.assertEqual(v.fingerprint(self.doc),v.fingerprint(self.doc))
    def test_invalid_surface_count_fails_closed(self):
        bad=dict(self.doc); bad["surfaces"]=bad["surfaces"][:-1]
        self.assertIn("surface_count_must_equal_100",v.validate(bad))
    def test_unknown_state_is_not_pass(self):
        self.assertNotEqual("UNKNOWN","PASS")

if __name__=="__main__": unittest.main()
