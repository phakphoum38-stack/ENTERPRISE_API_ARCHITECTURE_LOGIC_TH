import json
import tempfile
import unittest
from pathlib import Path

from research_os_v3.self_build import ResearchOSSelfBuilder, SelfBuildPolicy


class ResearchOSSelfBuildTests(unittest.TestCase):
    def _make_source(self, root: Path) -> None:
        required = (
            "v3/research_os_v3/orchestrator.py",
            "v3/research_os_v3/skills.py",
            "v3/research_os_v3/tools.py",
            "v3/flutter_app/pubspec.yaml",
            "v3/windows_service/ResearchOS.V3.ServiceHost.csproj",
        )
        for relative in required:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"fixture:{relative}\n", encoding="utf-8")
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "architecture.md").write_text("one truth\n", encoding="utf-8")
        (root / "v3" / "build").mkdir(parents=True, exist_ok=True)
        (root / "v3" / "build" / "generated.exe").write_bytes(b"generated")
        (root / "v3" / ".env").write_text("SECRET=do-not-copy\n", encoding="utf-8")
        (root / "v3" / "certificate.pfx").write_bytes(b"do-not-copy")

    def test_stage_copies_source_but_excludes_generated_and_secret_like_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            workspace = base / "workspace"
            source.mkdir()
            self._make_source(source)

            result = ResearchOSSelfBuilder(source).stage(workspace, source_sha="abc123")

            self.assertTrue((workspace / "v3/research_os_v3/orchestrator.py").is_file())
            self.assertTrue((workspace / "docs/architecture.md").is_file())
            self.assertFalse((workspace / "v3/build/generated.exe").exists())
            self.assertFalse((workspace / "v3/.env").exists())
            self.assertFalse((workspace / "v3/certificate.pfx").exists())

            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["contract"], "research-os-self-build-lab-v1")
            self.assertEqual(manifest["source_sha"], "abc123")
            self.assertEqual(manifest["file_count"], result.file_count)
            self.assertEqual(len(manifest["capabilities"]["tool_discovery_process"]), 7)
            self.assertEqual(manifest["capabilities"]["tool_discovery_process"][0]["skill"], "analysis")
            self.assertEqual(manifest["capabilities"]["tool_discovery_process"][4]["tool"], "drive-tools-list")

    def test_workspace_inside_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            self._make_source(source)
            builder = ResearchOSSelfBuilder(source)
            with self.assertRaises(ValueError):
                builder.stage(source / "nested-workspace")

    def test_existing_workspace_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            workspace = base / "workspace"
            source.mkdir()
            workspace.mkdir()
            self._make_source(source)
            with self.assertRaises(FileExistsError):
                ResearchOSSelfBuilder(source).stage(workspace)

    def test_missing_required_source_fails_closed_and_cleans_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            workspace = base / "workspace"
            source.mkdir()
            (source / "v3").mkdir()
            (source / "v3" / "README.md").write_text("incomplete\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                ResearchOSSelfBuilder(source).stage(workspace)
            self.assertFalse(workspace.exists())

    def test_custom_policy_cannot_escape_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            self._make_source(source)
            policy = SelfBuildPolicy(include_roots=("../outside",))
            with self.assertRaises(ValueError):
                ResearchOSSelfBuilder(source, policy).stage(base / "workspace")


if __name__ == "__main__":
    unittest.main()
