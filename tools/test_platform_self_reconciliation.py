import tempfile
import unittest
from pathlib import Path

from tools.platform_self_reconciliation import (
    build_plan,
    extract_local_references,
    is_protected,
    resolve_path,
    replace_reference,
    reconcile_sources,
)


class PlatformSelfReconciliationTest(unittest.TestCase):
    def test_exact_path_is_found(self):
        result = resolve_path("current/example.json", ["current/example.json", "docs/example.md"])
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.target, "current/example.json")

    def test_unique_wrong_path_is_relocatable(self):
        result = resolve_path("current/missing.json", ["tools/missing.json", "docs/other.md"])
        self.assertEqual(result.status, "RELOCATABLE")
        self.assertEqual(result.target, "tools/missing.json")

    def test_ambiguous_path_stops(self):
        result = resolve_path("current/missing.json", ["tools/missing.json", "docs/missing.json"])
        self.assertEqual(result.status, "AMBIGUOUS")
        self.assertIsNone(result.target)

    def test_missing_path_stops(self):
        result = resolve_path("current/missing.json", ["tools/other.py"])
        self.assertEqual(result.status, "MISSING")

    def test_protected_targets_cannot_be_auto_repaired(self):
        self.assertTrue(is_protected(".github/workflows/research-os-unified-final-gate.yml"))
        self.assertTrue(is_protected("current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"))
        self.assertFalse(is_protected("docs/example.md"))

    def test_reference_extraction_is_bounded_to_local_prefixes(self):
        text = '"current/a.json" "https://example.test/a" "tools/b.py"'
        self.assertEqual(
            extract_local_references(text),
            ("current/a.json", "tools/b.py"),
        )

    def test_plan_and_minimal_replacement(self):
        result = resolve_path("current/missing.json", ["tools/missing.json"])
        plan = build_plan("a" * 40, "docs/source.md", result)
        self.assertEqual(plan.confidence, "DETERMINISTIC")
        updated = replace_reference('"current/missing.json"', plan)
        self.assertEqual(updated, '"tools/missing.json"')

    def test_canonical_reconciliation_scan_has_canonical_sources(self):
        result = reconcile_sources()
        self.assertIn("current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json", result["sources"])
        self.assertIn("current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml", result["sources"])
        self.assertIn("current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json", result["sources"])
        self.assertEqual(result["component_registry"], "CONSUMED")
        self.assertIn(result["status"], {"PASS", "DRIFT"})

    def test_plan_rejects_ambiguous(self):
        result = resolve_path("current/missing.json", ["tools/missing.json", "docs/missing.json"])
        with self.assertRaises(ValueError):
            build_plan("a" * 40, "docs/source.md", result)


if __name__ == "__main__":
    unittest.main()
