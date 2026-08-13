import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research_os_v3 import DriveToolRuntimeAdapter, UnifiedToolRegistry


class DriveToolRuntimeTests(unittest.TestCase):
    def test_discovers_and_executes_checksum_verified_python_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "sample-tool"
            package.mkdir()
            entrypoint = package / "main.py"
            entrypoint.write_text(
                "import json, sys\npayload=json.load(sys.stdin)\nprint(json.dumps({'echo': payload.get('text'), 'ok': True}))\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(entrypoint.read_bytes()).hexdigest()
            (package / "tool.json").write_text(
                json.dumps(
                    {
                        "name": "sample-tool",
                        "version": "1.0.0",
                        "runtime": "python",
                        "entrypoint": "main.py",
                        "sha256": digest,
                        "timeout_seconds": 5,
                    }
                ),
                encoding="utf-8",
            )
            adapter = DriveToolRuntimeAdapter(root)
            self.assertTrue(adapter.available)
            self.assertEqual(adapter.discover()[0]["name"], "sample-tool")
            result = adapter.execute({"name": "sample-tool", "arguments": {"text": "drive-ok"}})
            self.assertEqual(result["exit_code"], 0)
            self.assertTrue(result["checksum_verified"])
            self.assertEqual(result["result"]["echo"], "drive-ok")

    def test_registry_requires_approval_for_drive_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = UnifiedToolRegistry(DriveToolRuntimeAdapter(Path(temporary)))
            self.assertIsNotNone(registry.get("drive-tools-list"))
            execute = registry.get("drive-tool-execute")
            self.assertIsNotNone(execute)
            self.assertTrue(execute.approval_required)
            with self.assertRaises(PermissionError):
                registry.execute("drive-tool-execute", {"name": "anything"})

    def test_checksum_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "bad-tool"
            package.mkdir()
            (package / "main.py").write_text("print('{}')\n", encoding="utf-8")
            (package / "tool.json").write_text(
                json.dumps(
                    {
                        "name": "bad-tool",
                        "version": "1.0.0",
                        "runtime": "python",
                        "entrypoint": "main.py",
                        "sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                DriveToolRuntimeAdapter(root).execute({"name": "bad-tool"})


if __name__ == "__main__":
    unittest.main()
