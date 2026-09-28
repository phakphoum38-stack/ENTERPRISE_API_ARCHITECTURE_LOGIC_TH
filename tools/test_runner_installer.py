from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.research_os_api.runner_installer import InstallationError, build_bootstrap_plan, install_verified_package, verify_manifest


class RunnerInstallerTests(unittest.TestCase):
    def _package(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        payload = root / "payload.txt"
        payload.write_text("Research OS\n", encoding="utf-8")
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        manifest = root / "PACKAGE_MANIFEST.json"
        manifest.write_text(json.dumps({
            "package_id": "research-os-test", "version": "1.0.0",
            "platform": "portable", "architecture": "host",
            "source_sha": "a" * 40, "artifact_sha256": digest,
            "files": {"payload.txt": digest}
        }, indent=2) + "\n", encoding="utf-8")
        return manifest

    def test_verified_package_installs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "package"
            manifest = self._package(package)
            target = root / "install"
            self.assertEqual(verify_manifest(package, manifest).package_id, "research-os-test")
            self.assertEqual(install_verified_package(package, manifest, target).version, "1.0.0")
            self.assertEqual((target / "payload.txt").read_text(encoding="utf-8"), "Research OS\n")

    def test_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            manifest = self._package(package)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"]["payload.txt"] = "0" * 64
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(InstallationError):
                verify_manifest(package, manifest)

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            manifest = self._package(package)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"]["../outside.txt"] = "0" * 64
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(InstallationError):
                verify_manifest(package, manifest)

    def test_bootstrap_plan_is_platform_neutral(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "cloud-drive"
            source.mkdir()
            plan = build_bootstrap_plan(source=source, platform_name="windows", architecture="x86_64")
            self.assertEqual(plan[-1], "READY")


if __name__ == "__main__":
    unittest.main()
