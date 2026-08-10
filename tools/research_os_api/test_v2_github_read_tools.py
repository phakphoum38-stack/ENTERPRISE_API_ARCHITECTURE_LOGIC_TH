#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, WorkingMemory
from v2_brain_runtime import BrainRuntime
from v2_github_read_tools import (
    GITHUB_READ_TOOLS_CONTRACT,
    install_github_read_tools,
)
from v2_skill_registry import SkillDefinition


class GitHubReadToolsTests(unittest.TestCase):
    def make_runtime(self, root: str) -> BrainRuntime:
        data = Path(root) / "runtime"
        data.mkdir()
        return BrainRuntime(
            registry=AgentRegistry(),
            working_memory=WorkingMemory(data),
            ledger=ActivityLedger(data),
        )

    @staticmethod
    def provider(repository: str):
        return {
            "repository": repository,
            "default_branch": "main",
            "commits": [{"sha": "abc1234", "message": "test"}],
            "pull_requests": [{"number": 19, "title": "Brain"}],
            "workflow_runs": [{"name": "CI", "status": "completed", "conclusion": "success"}],
            "credential_configured": False,
            "read_only": True,
        }

    def test_install_registers_one_read_only_network_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            pack = install_github_read_tools(runtime.tools, provider=self.provider)
            item = runtime.tools.describe("github.repository.dashboard")
            self.assertTrue(item["ready"])
            self.assertFalse(item["mutating"])
            self.assertTrue(item["network"])
            self.assertTrue(item["secret_access"])
            self.assertEqual(("github.read",), item["permissions"])
            status = pack.status()
            self.assertEqual(GITHUB_READ_TOOLS_CONTRACT, status["contract"])
            self.assertTrue(status["read_only"])
            self.assertFalse(status["write_actions_available"])

    def test_permission_gate_blocks_network_provider_before_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls = {"count": 0}

            def provider(repository: str):
                calls["count"] += 1
                return self.provider(repository)

            runtime = self.make_runtime(tmp)
            install_github_read_tools(runtime.tools, provider=provider)
            blocked = runtime.execute_tool(
                "github.repository.dashboard",
                "dashboard",
                session_id="github-read-blocked",
                payload={"repository": "owner/repo"},
            )
            self.assertEqual("blocked", blocked["status"])
            self.assertEqual(0, calls["count"])

    def test_dashboard_runs_without_approval_when_github_read_is_granted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            install_github_read_tools(runtime.tools, provider=self.provider)
            result = runtime.execute_tool(
                "github.repository.dashboard",
                "dashboard",
                session_id="github-read",
                payload={"repository": "owner/repo"},
                granted_permissions=("github.read",),
            )
            self.assertEqual("completed", result["status"])
            self.assertFalse(result["approval_required"])
            output = result["output"]
            self.assertEqual(GITHUB_READ_TOOLS_CONTRACT, output["contract"])
            self.assertEqual("owner/repo", output["repository"])
            self.assertTrue(output["read_only"])
            self.assertFalse(output["write_actions_available"])

    def test_repository_input_is_bounded_to_owner_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            pack = install_github_read_tools(runtime.tools, provider=self.provider)
            for invalid in ("", "owner", "https://github.com/owner/repo", "owner/repo/extra", ".owner/repo"):
                with self.subTest(invalid=invalid):
                    with self.assertRaises(ValueError):
                        pack.repository_dashboard({"repository": invalid})

    def test_secret_shaped_provider_output_is_scrubbed_by_execution_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)

            def provider(repository: str):
                return {
                    "repository": repository,
                    "message": "Authorization Bearer abcdefghijklmnopqrstuvwxyz",
                    "token_echo": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                }

            install_github_read_tools(runtime.tools, provider=provider)
            result = runtime.execute_tool(
                "github.repository.dashboard",
                "dashboard",
                session_id="github-secret-output",
                payload={"repository": "owner/repo"},
                granted_permissions=("github.read",),
            )
            self.assertEqual("completed", result["status"])
            rendered = repr(result)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz", rendered)
            self.assertNotIn("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", rendered)
            self.assertIn("[REDACTED]", rendered)

    def test_secret_shaped_provider_exception_is_scrubbed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)

            def provider(repository: str):
                del repository
                raise RuntimeError("GitHub failure Bearer abcdefghijklmnopqrstuvwxyz")

            install_github_read_tools(runtime.tools, provider=provider)
            result = runtime.execute_tool(
                "github.repository.dashboard",
                "dashboard",
                session_id="github-secret-error",
                payload={"repository": "owner/repo"},
                granted_permissions=("github.read",),
            )
            self.assertEqual("failed", result["status"])
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz", repr(result))
            self.assertIn("[REDACTED]", repr(result))

    def test_skill_executor_can_select_real_github_read_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            install_github_read_tools(runtime.tools, provider=self.provider)
            runtime.skills.register(
                SkillDefinition(
                    "developer.github-status-read",
                    "1.0.0",
                    "GitHub Status Read",
                    "Reads repository status through the governed Phase 5 GitHub adapter.",
                    ("github_status_read",),
                    required_tool_capabilities=("github_repository_read",),
                    permissions=("github.read",),
                    required_evidence=("repository", "read_only"),
                )
            )
            result = runtime.execute_skill(
                "developer.github-status-read",
                "dashboard",
                session_id="github-skill",
                payload={"repository": "owner/repo"},
                granted_permissions=("github.read",),
            )
            self.assertEqual("verified", result["status"])
            self.assertEqual("github.repository.dashboard", result["selected_tool_id"])
            self.assertTrue(result["verification"]["verified"])


if __name__ == "__main__":
    unittest.main()
