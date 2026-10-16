"""Regression tests for the Research OS local runner manager."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ResearchOSLocalRunnerManager as manager


class RunnerManagerHelperTests(unittest.TestCase):
    def test_settings_round_trip_persists_preferences_not_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            with mock.patch.object(manager, "settings_path", return_value=path):
                manager.save_settings({
                    "account": "example-user",
                    "repository": "example-user/example-repo",
                    "installer_path": "D:/trusted/Install-ResearchOSLocalRunner.ps1",
                })
                saved = path.read_text(encoding="utf-8")
                loaded = manager.load_settings()

            self.assertEqual(loaded["account"], "example-user")
            self.assertEqual(loaded["repository"], "example-user/example-repo")
            self.assertNotIn("GH_TOKEN", saved)
            self.assertNotIn("ghp_", saved)

    def test_repository_discovery_uses_selected_account_token_without_switching(self) -> None:
        result = subprocess.CompletedProcess(
            args=["gh", "api"], returncode=0,
            stdout="example-user/zeta\nexample-user/alpha\nbad value\n",
            stderr=None,
        )
        env_snapshot: dict[str, str] = {}
        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            supplied_env = kwargs.get("env")
            if isinstance(supplied_env, dict):
                env_snapshot.update(supplied_env)
            return result

        original_token = os.environ.get("GH_TOKEN")
        with mock.patch.object(manager, "account_token", return_value="test-secret-token"), \
             mock.patch.object(manager, "run_command", side_effect=fake_run) as run:
            repositories = manager.repositories_for("example-user")

        self.assertEqual(repositories, ["example-user/alpha", "example-user/zeta"])
        args, _kwargs = run.call_args
        self.assertEqual(args[0][:3], ["gh", "api", "user/repos"])
        self.assertEqual(env_snapshot["GH_TOKEN"], "test-secret-token")
        self.assertEqual(os.environ.get("GH_TOKEN"), original_token)
        self.assertNotIn("auth", args[0])

    def test_repository_discovery_rejects_invalid_lines(self) -> None:
        result = subprocess.CompletedProcess(
            args=["gh", "api"], returncode=0,
            stdout="owner/repo\nnot-a-repository\nowner/repo\n",
            stderr=None,
        )
        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            return result

        with mock.patch.object(manager, "account_token", return_value="test-secret-token"), \
             mock.patch.object(manager, "run_command", side_effect=fake_run):
            repositories = manager.repositories_for("example-user")

        self.assertEqual(repositories, ["owner/repo"])

    def test_account_token_never_returns_command_error_text_as_token(self) -> None:
        result = subprocess.CompletedProcess(
            args=["gh", "auth", "token"], returncode=1,
            stdout="authentication failed", stderr=None,
        )
        with mock.patch.object(manager, "run_command", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "Could not obtain a credential"):
                manager.account_token("example-user")


if __name__ == "__main__":
    unittest.main()
