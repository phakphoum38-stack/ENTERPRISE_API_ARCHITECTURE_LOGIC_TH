import json,unittest
from pathlib import Path
from tools.validate_platform_virtual_workspace import validate
ROOT=Path(__file__).resolve().parents[2]
class PlatformVirtualWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((ROOT/"current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json").read_text())
        self.r=json.loads((ROOT/"current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json").read_text())
    def test_registry_is_single_logical_workspace(self):
        self.assertEqual(self.c["storage_model"],"single_registry")
        self.assertFalse(self.c["resource_policy"]["new_directories_required"])
    def test_all_platform_categories_are_registered(self):
        self.assertEqual({x["category"] for x in self.r["records"]},set(self.c["categories"]))
    def test_records_have_locator_and_lineage(self):
        for x in self.r["records"]:
            self.assertTrue(x["virtual_path"].startswith("PLATFORM/"))
            self.assertTrue(x["source_refs"])
    def test_unknown_is_not_done(self):
        for x in self.r["records"]:
            if x["resolution"]=="UNKNOWN":self.assertNotEqual(x["status"],"DONE")
    def test_authority_is_descriptive_only(self):
        self.assertFalse(self.c["authority"]["may_merge"])
        self.assertFalse(self.c["authority"]["may_approve"])
    def test_validator_passes(self):
        self.assertEqual(len(validate(self.c,self.r)),64)
    def test_no_duplicate_ids(self):
        ids=[x["work_id"] for x in self.r["records"]];self.assertEqual(len(ids),len(set(ids)))
if __name__=="__main__":unittest.main()
