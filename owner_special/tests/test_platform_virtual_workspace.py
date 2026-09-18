import json
import unittest
from pathlib import Path

from tools.platform_graph import Edge, Node, PlatformGraph
from tools.validate_platform_virtual_workspace import validate

ROOT = Path(__file__).resolve().parents[2]


class PlatformVirtualWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.c = json.loads((ROOT / "current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json").read_text())
        self.r = json.loads((ROOT / "current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json").read_text())
        self.g = PlatformGraph(self.c, self.r)

    def test_registry_is_single_logical_workspace(self):
        self.assertEqual(self.c["storage_model"], "single_registry")
        self.assertFalse(self.c["resource_policy"]["new_directories_required"])

    def test_all_platform_categories_are_registered(self):
        self.assertEqual({x["category"] for x in self.r["records"]}, set(self.c["categories"]))

    def test_records_have_locator_and_lineage(self):
        for x in self.r["records"]:
            self.assertTrue(x["virtual_path"].startswith("PLATFORM/"))
            self.assertTrue(x["source_refs"])

    def test_unknown_is_not_done(self):
        for x in self.r["records"]:
            if x["resolution"] == "UNKNOWN":
                self.assertNotEqual(x["status"], "DONE")

    def test_authority_is_descriptive_only(self):
        self.assertFalse(self.c["authority"]["may_merge"])
        self.assertFalse(self.c["authority"]["may_approve"])

    def test_validator_passes(self):
        self.assertEqual(len(validate(self.c, self.r)), 64)

    def test_no_duplicate_ids(self):
        ids = [x["work_id"] for x in self.r["records"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_engine_loads_existing_workspace(self):
        self.assertEqual(len(self.g.find(kind="WORK")), len(self.r["records"]))
        self.assertGreaterEqual(len(self.g.edges), len(self.r["records"]))

    def test_engine_trace_is_bounded(self):
        result = self.g.trace("PLATFORM-002", depth=1)
        self.assertEqual(result[0], "PLATFORM-002")
        self.assertLessEqual(len(result), 10)

    def test_engine_rejects_unknown_relation(self):
        with self.assertRaises(ValueError):
            self.g.add_edge(Edge("A", "NOT_A_RELATION", "B"))

    def test_engine_rejects_duplicate_node(self):
        with self.assertRaises(ValueError):
            self.g.add_node(Node("PLATFORM-001", "WORK"))

    def test_engine_explain_is_descriptive(self):
        result = self.g.explain("PLATFORM-002")
        self.assertEqual(result["node"]["id"], "PLATFORM-002")
        self.assertFalse(result["authority"]["may_merge"])
        self.assertFalse(result["authority"]["may_approve"])

    def test_engine_summary_declares_logical_not_physical_space(self):
        summary = self.g.summary()
        self.assertEqual(summary["logical_space"], "10^10+ (bounded, on-demand)")
        self.assertEqual(summary["materialization"], "forbidden")
        self.assertEqual(summary["authority"], "descriptive_only")


if __name__ == "__main__":
    unittest.main()
