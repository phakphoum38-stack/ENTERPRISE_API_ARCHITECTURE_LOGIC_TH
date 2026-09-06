import unittest

from repair_diff_pipeline import validate_diff


SAFE_DIFF = """diff --git a/tools/example.py b/tools/example.py
--- a/tools/example.py
+++ b/tools/example.py
@@ -1 +1 @@
-old = 1
+new = 2
"""


class RepairDiffPipelineTests(unittest.TestCase):
    def test_valid_unified_diff_passes(self):
        result = validate_diff(SAFE_DIFF)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["files"], ["tools/example.py"])
        self.assertFalse(result["apply_to_main"])
        self.assertFalse(result["auto_merge"])

    def test_empty_diff_fails(self):
        result = validate_diff("")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("repair diff is empty", result["errors"])

    def test_missing_headers_fail(self):
        result = validate_diff("@@ -1 +1 @@\n-old\n+new\n")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("no unified-diff file headers found", result["errors"])

    def test_protected_workflow_is_rejected(self):
        diff = SAFE_DIFF.replace("tools/example.py", ".github/workflows/release.yml")
        result = validate_diff(diff)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("protected file" in e for e in result["errors"]))

    def test_parent_escape_is_rejected(self):
        diff = SAFE_DIFF.replace("tools/example.py", "../escape.py")
        result = validate_diff(diff)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("unsafe diff path" in e for e in result["errors"]))

    def test_absolute_path_is_rejected(self):
        diff = SAFE_DIFF.replace("tools/example.py", "/tmp/escape.py")
        result = validate_diff(diff)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("unsafe diff path" in e for e in result["errors"]))

    def test_metadata_contains_content_hash(self):
        result = validate_diff(SAFE_DIFF)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertEqual(result["bytes"], len(SAFE_DIFF.encode("utf-8")))


if __name__ == "__main__":
    unittest.main()
