#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, WorkingMemory
from v2_brain_runtime import BrainRuntime
from v2_developer_action_tools import CommandProfile, install_developer_action_tools
from v2_github_write_tools import install_github_write_tools
from v2_skill_registry import SkillDefinition
from v2_workspace_tools import WorkspaceBoundaryError


class DeveloperActionsPhase6Tests(unittest.TestCase):
    def runtime(self, root: str) -> BrainRuntime:
        data = Path(root) / ".runtime"
        data.mkdir(exist_ok=True)
        return BrainRuntime(
            registry=AgentRegistry(),
            working_memory=WorkingMemory(data),
            ledger=ActivityLedger(data),
        )

    @staticmethod
    def seed(root: str) -> None:
        base = Path(root)
        (base / "lib").mkdir()
        (base / "lib" / "app.py").write_text("value = 1\n", encoding="utf-8")
        (base / ".env").write_text("TOKEN=blocked\n", encoding="utf-8")

    def test_workspace_write_is_preview_bound_and_approval_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed(tmp)
            runtime = self.runtime(tmp)
            install_developer_action_tools(runtime.tools, tmp)
            payload = {"path": "lib/app.py", "content": "value = 2\n"}

            preview = runtime.execute_tool(
                "workspace.file.change", "write", session_id="write-preview", payload=payload,
                granted_permissions=("workspace.read", "workspace.write"), dry_run=True,
            )
            self.assertEqual("completed", preview["status"])
            self.assertIn("-value = 1", preview["output"]["diff"])
            self.assertIn("+value = 2", preview["output"]["diff"])
            fingerprint = preview["output"]["approval_fingerprint"]

            waiting = runtime.execute_tool(
                "workspace.file.change", "write", session_id="write-apply",
                payload={**payload, "approval_fingerprint": fingerprint},
                granted_permissions=("workspace.read", "workspace.write"),
            )
            self.assertEqual("awaiting_approval", waiting["status"])
            self.assertEqual("value = 1\n", (Path(tmp) / "lib" / "app.py").read_text())

            done = runtime.execute_tool(
                "workspace.file.change", "write", session_id="write-apply",
                payload={**payload, "approval_fingerprint": fingerprint},
                granted_permissions=("workspace.read", "workspace.write"), approved=True,
            )
            self.assertEqual("completed", done["status"])
            self.assertTrue(done["output"]["verification"]["matches"])
            self.assertEqual("value = 2\n", (Path(tmp) / "lib" / "app.py").read_text())

    def test_workspace_change_fails_closed_on_stale_fingerprint_and_secret_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed(tmp)
            runtime = self.runtime(tmp)
            pack = install_developer_action_tools(runtime.tools, tmp)
            payload = {"path": "lib/app.py", "content": "value = 2\n"}
            preview = runtime.execute_tool(
                "workspace.file.change", "write", session_id="stale-preview", payload=payload,
                granted_permissions=("workspace.read", "workspace.write"), dry_run=True,
            )
            (Path(tmp) / "lib" / "app.py").write_text("value = 99\n", encoding="utf-8")
            failed = runtime.execute_tool(
                "workspace.file.change", "write", session_id="stale-apply",
                payload={**payload, "approval_fingerprint": preview["output"]["approval_fingerprint"]},
                granted_permissions=("workspace.read", "workspace.write"), approved=True,
            )
            self.assertEqual("failed", failed["status"])
            self.assertIn("approval_fingerprint mismatch", failed["error"])
            with self.assertRaises(WorkspaceBoundaryError):
                pack.file_change("write", {"path": ".env", "content": "x=1\n"}, dry_run=True)
            with self.assertRaises(WorkspaceBoundaryError):
                pack.file_change("write", {"path": "../x.py", "content": "x=1\n"}, dry_run=True)

    def test_controlled_commands_ignore_payload_argv_and_strip_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.seed(tmp)
            runtime = self.runtime(tmp)
            calls: list[dict] = []

            def executor(profile, cwd, env):
                calls.append({"argv": profile.argv, "env": dict(env), "cwd": cwd})
                return {"returncode": 0, "stdout": "ok", "stderr": ""}

            profile = CommandProfile(
                "unit.test", ("python", "-m", "unittest", "discover"),
                timeout_seconds=30, category="test",
            )
            install_developer_action_tools(
                runtime.tools, tmp, command_profiles=(profile,), command_executor=executor,
            )
            payload = {"command_id": "unit.test", "argv": ["unexpected", "payload"]}
            preview = runtime.execute_tool(
                "workspace.command.run", "run", session_id="command-preview", payload=payload,
                granted_permissions=("workspace.execute",), dry_run=True,
            )
            self.assertEqual(["python", "-m", "unittest", "discover"], preview["output"]["argv"])
            self.assertEqual([], calls)

            with patch.dict(os.environ, {"GITHUB_TOKEN": "must-not-inherit", "API_KEY": "blocked"}, clear=False):
                done = runtime.execute_tool(
                    "workspace.command.run", "run", session_id="command-apply", payload=payload,
                    granted_permissions=("workspace.execute",), approved=True,
                )
            self.assertEqual("completed", done["status"])
            self.assertNotIn("GITHUB_TOKEN", calls[0]["env"])
            self.assertNotIn("API_KEY", calls[0]["env"])
            self.assertEqual(("python", "-m", "unittest", "discover"), calls[0]["argv"])

    def test_github_file_write_blocks_protected_branches_and_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.runtime(tmp)
            calls: list[tuple[str, dict]] = []

            def provider(action, payload):
                calls.append((action, dict(payload)))
                return {"commit_sha": "a" * 40, "content_sha": "b" * 40}

            pack = install_github_write_tools(runtime.tools, provider=provider)
            base = {
                "repository": "owner/repo", "path": "lib/app.py", "content": "value = 2\n",
                "message": "feat: update app", "expected_sha": "c" * 40,
            }
            for branch in ("main", "release/v2.0.0-rc.1", "deploy/production"):
                with self.assertRaisesRegex(ValueError, "protected GitHub branch"):
                    pack.file_upsert({**base, "branch": branch}, dry_run=True)

            payload = {**base, "branch": "feature/phase6"}
            preview = runtime.execute_tool(
                "github.branch.file.upsert", "upsert", session_id="github-preview", payload=payload,
                granted_permissions=("github.write",), dry_run=True,
            )
            self.assertEqual([], calls)
            fingerprint = preview["output"]["approval_fingerprint"]
            waiting = runtime.execute_tool(
                "github.branch.file.upsert", "upsert", session_id="github-apply",
                payload={**payload, "approval_fingerprint": fingerprint},
                granted_permissions=("github.write",),
            )
            self.assertEqual("awaiting_approval", waiting["status"])
            self.assertEqual([], calls)
            done = runtime.execute_tool(
                "github.branch.file.upsert", "upsert", session_id="github-apply",
                payload={**payload, "approval_fingerprint": fingerprint},
                granted_permissions=("github.write",), approved=True,
            )
            self.assertEqual("completed", done["status"])
            self.assertEqual("file_upsert", calls[0][0])
            self.assertFalse(pack.status()["merge_available"])
            self.assertFalse(pack.status()["release_available"])
            self.assertFalse(pack.status()["deployment_available"])

    def test_github_comment_skill_verifies_without_code_state_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.runtime(tmp)
            install_github_write_tools(runtime.tools, provider=lambda action, payload: {"comment_id": 9001})
            runtime.skills.register(
                SkillDefinition(
                    "github.pr-comment", "1.0.0", "GitHub PR Comment", "Adds a governed PR comment.",
                    ("github_pr_feedback",), required_tool_capabilities=("github_pull_request_comment",),
                    permissions=("github.write",), required_evidence=("applied", "comment_id"),
                )
            )
            payload = {"repository": "owner/repo", "pr_number": 19, "comment": "review evidence attached"}
            preview = runtime.execute_tool(
                "github.pull_request.comment", "comment", session_id="comment-preview", payload=payload,
                granted_permissions=("github.write",), dry_run=True,
            )
            result = runtime.execute_skill(
                "github.pr-comment", "comment", session_id="comment-skill",
                payload={**payload, "approval_fingerprint": preview["output"]["approval_fingerprint"]},
                granted_permissions=("github.write",), approved=True,
            )
            self.assertEqual("verified", result["status"])
            self.assertEqual("github.pull_request.comment", result["selected_tool_id"])

    def test_github_provider_reflection_is_secret_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.runtime(tmp)
            secret = "phase6-provider-secret"
            install_github_write_tools(
                runtime.tools, provider=lambda action, payload: {"commit_sha": "d" * 40, "echo": secret},
            )
            payload = {
                "repository": "owner/repo", "branch": "feature/redaction", "path": "app.py",
                "content": "x=1\n", "message": "test", "expected_sha": "e" * 40,
            }
            preview = runtime.execute_tool(
                "github.branch.file.upsert", "upsert", session_id="redaction-preview", payload=payload,
                granted_permissions=("github.write",), dry_run=True,
            )
            done = runtime.execute_tool(
                "github.branch.file.upsert", "upsert", session_id="redaction-apply",
                payload={**payload, "approval_fingerprint": preview["output"]["approval_fingerprint"]},
                granted_permissions=("github.write",), approved=True, secret_values=(secret,),
            )
            self.assertEqual("completed", done["status"])
            self.assertNotIn(secret, str(done))
            self.assertEqual("[REDACTED]", done["output"]["result"]["echo"])


if __name__ == "__main__":
    unittest.main()
