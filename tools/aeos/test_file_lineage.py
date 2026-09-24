import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from file_lineage import verify


class FileLineageTests(unittest.TestCase):
    def _repo(self):
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "aeos@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "AEOS"], cwd=root, check=True)
        (root / "root.txt").write_text("root\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "root"], cwd=root, check=True, capture_output=True)
        base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        return root, base

    def test_modified_has_existing_lineage(self):
        root, base = self._repo()
        (root / "root.txt").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-am", "modify"], cwd=root, check=True, capture_output=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        results = verify(root, base, head, {"entries": {}})
        self.assertEqual(results[0].status, "MODIFIED")
        self.assertIsNone(results[0].fail_code)

    def test_added_without_evidence_is_blocking(self):
        root, base = self._repo()
        (root / "new.txt").write_text("new\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "new"], cwd=root, check=True, capture_output=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        results = verify(root, base, head, {"entries": {}})
        self.assertEqual(results[0].status, "ORPHAN_ADDED")
        self.assertEqual(results[0].fail_code, "AEOS-LINEAGE-ORPHAN")

    def test_added_genesis_requires_explicit_manifest(self):
        root, base = self._repo()
        (root / "new.txt").write_text("new\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "new"], cwd=root, check=True, capture_output=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        results = verify(root, base, head, {"entries": {"new.txt": {"kind": "genesis", "lineage_root": "new.txt"}}})
        self.assertEqual(results[0].status, "ADDED_GENESIS")

    def test_rename_records_predecessor(self):
        root, base = self._repo()
        (root / "renamed.txt").write_text((root / "root.txt").read_text(), encoding="utf-8")
        (root / "root.txt").unlink()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "rename"], cwd=root, check=True, capture_output=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        results = verify(root, base, head, {"entries": {}})
        self.assertEqual(results[0].status, "RENAMED")
        self.assertEqual(results[0].expected_parent, "root.txt")


if __name__ == "__main__":
    unittest.main()
