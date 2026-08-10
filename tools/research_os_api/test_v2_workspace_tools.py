#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, WorkingMemory
from v2_brain_runtime import BrainRuntime
from v2_skill_registry import SkillDefinition
from v2_workspace_tools import (
    WORKSPACE_READ_TOOL_DEFINITIONS,
    WORKSPACE_READ_TOOLS_CONTRACT,
    WorkspaceBoundaryError,
    install_workspace_read_tools,
)


class WorkspaceReadToolsTests(unittest.TestCase):
    def make_runtime(self, root: str) -> BrainRuntime:
        runtime_data = Path(root) / ".runtime-data"
        runtime_data.mkdir()
        return BrainRuntime(
            registry=AgentRegistry(),
            working_memory=WorkingMemory(runtime_data),
            ledger=ActivityLedger(runtime_data),
        )

    @staticmethod
    def seed_workspace(root: str) -> None:
        base = Path(root)
        (base / "lib").mkdir()
        (base / "test").mkdir()
        (base / ".github" / "workflows").mkdir(parents=True)
        (base / "build").mkdir()
        (base / "node_modules").mkdir()
        (base / "lib" / "app.py").write_text(
            "def hello():\n    return 'Research OS'\n",
            encoding="utf-8",
        )
        (base / "lib" / "other.py").write_text(
            "from app import hello\nprint(hello())\n",
            encoding="utf-8",
        )
        (base / "test" / "test_app.py").write_text(
            "def test_hello():\n    assert True\n",
            encoding="utf-8",
        )
        (base / "pyproject.toml").write_text("[project]\nname='brain-fixture'\n", encoding="utf-8")
        (base / ".github" / "workflows" / "ci.yml").write_text(
            "name: CI\non: [push]\n",
            encoding="utf-8",
        )
        (base / ".env").write_text("API_KEY=must-never-be-readable\n", encoding="utf-8")
        (base / ".env.example").write_text("API_KEY=example-only\n", encoding="utf-8")
        (base / "build" / "generated.py").write_text("Research OS generated\n", encoding="utf-8")
        (base / "node_modules" / "ignored.js").write_text("Research OS dependency\n", encoding="utf-8")

    def test_install_registers_five_real_read_only_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            runtime = self.make_runtime(tmp)
            pack = install_workspace_read_tools(runtime.tools, tmp)
            report = runtime.introspect()["tools"]
            workspace_ids = {item.tool_id for item in WORKSPACE_READ_TOOL_DEFINITIONS}
            registered = {item["tool_id"] for item in report["tools"] if item["tool_id"].startswith("workspace.")}
            self.assertEqual(workspace_ids, registered)
            self.assertTrue(all(runtime.tools.describe(tool_id)["ready"] for tool_id in workspace_ids))
            self.assertEqual(WORKSPACE_READ_TOOLS_CONTRACT, pack.status()["contract"])
            self.assertTrue(pack.status()["read_only"])
            self.assertFalse(pack.status()["shell_execution"])
            self.assertFalse(pack.status()["network"])

    def test_file_read_runs_through_brain_permission_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            runtime = self.make_runtime(tmp)
            install_workspace_read_tools(runtime.tools, tmp)

            blocked = runtime.execute_tool(
                "workspace.file.read",
                "read",
                session_id="workspace-read",
                payload={"path": "lib/app.py"},
            )
            self.assertEqual("blocked", blocked["status"])

            completed = runtime.execute_tool(
                "workspace.file.read",
                "read",
                session_id="workspace-read",
                payload={"path": "lib/app.py"},
                granted_permissions=("workspace.read",),
            )
            self.assertEqual("completed", completed["status"])
            self.assertEqual("lib/app.py", completed["output"]["path"])
            self.assertIn("Research OS", completed["output"]["content"])
            self.assertTrue(completed["output"]["read_only"])

    def test_parent_traversal_absolute_and_secret_paths_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            runtime = self.make_runtime(tmp)
            pack = install_workspace_read_tools(runtime.tools, tmp)
            with self.assertRaises(WorkspaceBoundaryError):
                pack.read_file({"path": "../outside.txt"})
            with self.assertRaises(WorkspaceBoundaryError):
                pack.read_file({"path": str(Path(tmp).resolve() / "lib" / "app.py")})
            with self.assertRaises(WorkspaceBoundaryError):
                pack.read_file({"path": ".env"})
            allowed = pack.read_file({"path": ".env.example"})
            self.assertIn("example-only", allowed["content"])

    def test_code_search_is_bounded_and_skips_generated_dependency_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            runtime = self.make_runtime(tmp)
            install_workspace_read_tools(runtime.tools, tmp)
            result = runtime.execute_tool(
                "workspace.code.search",
                "search",
                session_id="search",
                payload={"query": "Research OS", "limit": 20},
                granted_permissions=("workspace.read",),
            )
            self.assertEqual("completed", result["status"])
            paths = {item["path"] for item in result["output"]["matches"]}
            self.assertIn("lib/app.py", paths)
            self.assertNotIn("build/generated.py", paths)
            self.assertNotIn("node_modules/ignored.js", paths)
            self.assertNotIn(".env", paths)

    def test_repository_map_omits_secret_and_ignored_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            runtime = self.make_runtime(tmp)
            install_workspace_read_tools(runtime.tools, tmp)
            result = runtime.execute_tool(
                "workspace.repository.map",
                "map",
                session_id="map",
                payload={"max_depth": 5},
                granted_permissions=("workspace.read",),
            )
            self.assertEqual("completed", result["status"])
            paths = {item["path"] for item in result["output"]["entries"]}
            self.assertIn("lib/app.py", paths)
            self.assertNotIn(".env", paths)
            self.assertFalse(any(path.startswith("build/") for path in paths))
            self.assertFalse(any(path.startswith("node_modules/") for path in paths))

    def test_build_inspector_detects_manifests_workflows_and_tests_without_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            runtime = self.make_runtime(tmp)
            install_workspace_read_tools(runtime.tools, tmp)
            result = runtime.execute_tool(
                "workspace.build.inspect",
                "inspect",
                session_id="build-inspect",
                granted_permissions=("workspace.read",),
            )
            self.assertEqual("completed", result["status"])
            output = result["output"]
            self.assertIn("pyproject.toml", output["manifests"])
            self.assertIn(".github/workflows/ci.yml", output["workflows"])
            self.assertIn("test/test_app.py", output["tests"])
            self.assertEqual(0, output["commands_executed"])
            self.assertTrue(output["read_only"])

    def test_skill_executor_can_use_real_workspace_file_adapter_and_verify_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            runtime = self.make_runtime(tmp)
            install_workspace_read_tools(runtime.tools, tmp)
            runtime.skills.register(
                SkillDefinition(
                    "developer.workspace-file-read",
                    "1.0.0",
                    "Workspace File Read",
                    "Reads source through the governed Phase 5 workspace adapter.",
                    ("workspace_source_read",),
                    required_tool_capabilities=("workspace_file_read",),
                    permissions=("workspace.read",),
                    required_evidence=("content", "path", "read_only"),
                )
            )
            result = runtime.execute_skill(
                "developer.workspace-file-read",
                "read",
                session_id="skill-workspace-read",
                payload={"path": "lib/app.py"},
                granted_permissions=("workspace.read",),
            )
            self.assertEqual("verified", result["status"])
            self.assertEqual("workspace.file.read", result["selected_tool_id"])
            self.assertTrue(result["verification"]["verified"])

    def test_binary_and_oversized_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_workspace(tmp)
            (Path(tmp) / "image.bin").write_bytes(b"abc\x00def")
            (Path(tmp) / "large.txt").write_text("x" * 4096, encoding="utf-8")
            runtime = self.make_runtime(tmp)
            pack = install_workspace_read_tools(runtime.tools, tmp, max_read_bytes=1024)
            with self.assertRaisesRegex(ValueError, "binary"):
                pack.read_file({"path": "image.bin"})
            with self.assertRaisesRegex(ValueError, "exceeds read limit"):
                pack.read_file({"path": "large.txt"})


if __name__ == "__main__":
    unittest.main()
