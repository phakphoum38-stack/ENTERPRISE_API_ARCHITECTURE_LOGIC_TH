from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import flutter_code_tool as tool


class FlutterCodeToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        project = self.root / "apps" / "research_os_flutter"
        project.mkdir(parents=True)
        (project / "lib").mkdir()
        (project / "lib" / "main.dart").write_text("void main() {}\n", encoding="utf-8")
        self.env = patch.dict(os.environ, {
            "RESEARCH_OS_CODE_ROOT": str(self.root),
            "RESEARCH_OS_CODE_OWNER_IDS": "owner@example.com",
            "RESEARCH_OS_FLUTTER_COMMAND": "flutter",
        })
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def test_project_and_file_read(self) -> None:
        projects = tool.project_map()
        self.assertIn("research_os_flutter", projects)
        payload = tool.read_file("research_os_flutter", "lib/main.dart")
        self.assertEqual(payload["content"], "void main() {}\n")

    def test_rejects_absolute_and_parent_paths(self) -> None:
        with self.assertRaises(ValueError):
            tool.read_file("research_os_flutter", "../secret.dart")
        with self.assertRaises(ValueError):
            tool.read_file("research_os_flutter", "/secret.dart")

    def test_preview_is_sha_bound(self) -> None:
        current = tool.read_file("research_os_flutter", "lib/main.dart")
        preview = tool.preview("research_os_flutter", "lib/main.dart", current["sha256"], "void main() { print(1); }\n")
        self.assertTrue(preview["changed"])
        self.assertIn("+void main()", preview["diff"])

    @patch("flutter_code_tool.validate", return_value={"ok": True, "steps": []})
    def test_apply_requires_owner_and_validates(self, validate) -> None:
        current = tool.read_file("research_os_flutter", "lib/main.dart")
        result = tool.apply("research_os_flutter", "lib/main.dart", current["sha256"], "void main() { print(1); }\n", "owner@example.com")
        self.assertTrue(result["applied"])
        validate.assert_called_once()

    def test_non_owner_cannot_apply(self) -> None:
        current = tool.read_file("research_os_flutter", "lib/main.dart")
        with self.assertRaises(PermissionError):
            tool.apply("research_os_flutter", "lib/main.dart", current["sha256"], "x\n", "dev@example.com")


if __name__ == "__main__":
    unittest.main()
