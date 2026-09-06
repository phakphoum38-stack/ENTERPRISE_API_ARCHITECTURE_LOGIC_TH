from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from file_audit_v6x6 import MAX_LEAF_CAPACITY, audit_repository, logical_capacity


class FileAuditV6x6Tests(unittest.TestCase):
    def test_capacity_is_exactly_6_to_the_6(self) -> None:
        capacity = logical_capacity()
        self.assertEqual(capacity["branching_factor"], 6)
        self.assertEqual(capacity["depth"], 6)
        self.assertEqual(capacity["max_leaf_capacity"], 46656)
        self.assertEqual(MAX_LEAF_CAPACITY, 6**6)

    def test_detects_invalid_json_and_merge_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "good.py").write_text("value = 1\n", encoding="utf-8")
            (root / "bad.json").write_text('{"broken": }\n', encoding="utf-8")
            (root / "conflict.txt").write_text(
                "<<<<<<< HEAD\na\n=======\nb\n>>>>>>> branch\n",
                encoding="utf-8",
            )
            report = audit_repository(root, workers=2)

        codes = {item["code"] for item in report["findings"]}
        self.assertIn("invalid-json", codes)
        self.assertIn("merge-marker", codes)
        self.assertEqual(report["contract"], "adaptive-file-audit-v6x6")
        self.assertEqual(report["capacity"]["max_leaf_capacity"], 46656)

    def test_decorative_separator_is_not_a_merge_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "generated.txt").write_text(
                "Purpose\n=======\nGenerated document\n\nSafety\n===============\n",
                encoding="utf-8",
            )
            report = audit_repository(root, workers=1)

        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["findings"], [])

    def test_clean_tree_has_no_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "b.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
            report = audit_repository(root, workers=2)

        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["files_scanned"], 2)


if __name__ == "__main__":
    unittest.main()
