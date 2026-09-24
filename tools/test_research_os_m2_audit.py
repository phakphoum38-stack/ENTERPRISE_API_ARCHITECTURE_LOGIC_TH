import unittest
from tools.research_os_m2_audit import build_index

class M2AuditIndexTests(unittest.TestCase):
    def test_index_is_source_pinned_and_integrity_complete(self):
        index=build_index()
        self.assertRegex(index["source_sha"],r"^[0-9a-f]{40}$")
        self.assertGreater(index["inventory"]["files"],0)
        self.assertTrue(all(index["integrity"].values()))
    def test_expected_capabilities_are_discoverable(self):
        rows={r["path"]:r for r in build_index()["files"]}
        self.assertIn("current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",rows)
        self.assertIn("tools/research_os_m2_audit.py",rows)
        self.assertIn("apps/research_os_flutter/lib/src/features/control_center/native_control_center_page.dart",rows)
        self.assertIn("final_gate",rows["current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"]["capabilities"])
    def test_query_returns_relevant_records(self):
        matches=[r for r in build_index()["files"] if "runner" in (r["path"]+" "+" ".join(r["capabilities"])).lower()]
        self.assertTrue(matches)
        self.assertTrue(any("runner" in r["path"].lower() for r in matches))
if __name__=="__main__": unittest.main()
