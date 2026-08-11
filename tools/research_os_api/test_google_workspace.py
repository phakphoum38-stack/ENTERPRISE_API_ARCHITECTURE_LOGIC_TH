import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from google_workspace import GoogleWorkspaceConfig, WORKSPACE_SERVICES


class GoogleWorkspaceConfigTest(unittest.TestCase):
    def test_all_services_present_and_not_configured_without_oauth(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            config = GoogleWorkspaceConfig(tmp)
            dashboard = config.dashboard()
            self.assertEqual(dashboard["total_count"], len(WORKSPACE_SERVICES))
            self.assertEqual(dashboard["enabled_count"], len(WORKSPACE_SERVICES))
            self.assertFalse(dashboard["oauth_configured"])
            self.assertFalse(dashboard["app_access"])
            self.assertFalse(dashboard["local_account_accepted"])
            self.assertEqual(dashboard["account_mode"], "none")
            self.assertTrue(all(item["state"] == "not_configured" for item in dashboard["services"]))
            self.assertEqual(dashboard["token_storage"], "backend_only")

    def test_oauth_ready_when_client_credentials_exist(self):
        env = {
            "RESEARCH_OS_GOOGLE_CLIENT_ID": "client-id",
            "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "client-secret",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            config = GoogleWorkspaceConfig(tmp)
            states = {item["state"] for item in config.dashboard()["services"]}
            self.assertEqual(states, {"ready_for_oauth"})

    def test_enabled_services_are_persisted_locally(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            config = GoogleWorkspaceConfig(tmp)
            config.set_enabled_services(["drive", "sheets", "calendar"])
            status = {item.service: item for item in config.statuses()}
            self.assertTrue(status["drive"].enabled)
            self.assertFalse(status["gmail"].enabled)
            self.assertEqual(status["gmail"].state, "disabled")
            self.assertTrue((Path(tmp) / "google_workspace" / "settings.json").exists())

    def test_local_account_acceptance_enables_app_access_without_google_token(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            config = GoogleWorkspaceConfig(tmp)
            dashboard = config.accept_local_account()
            self.assertTrue(dashboard["app_access"])
            self.assertTrue(dashboard["local_account_accepted"])
            self.assertEqual(dashboard["account_mode"], "local")
            self.assertFalse(dashboard["connected"])
            self.assertFalse((Path(tmp) / "google_workspace" / "oauth_token.json").exists())
            self.assertTrue((Path(tmp) / "google_workspace" / "local_account.json").exists())


if __name__ == "__main__":
    unittest.main()
