from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from developer_server import DeveloperPlatformHandler


class DeveloperPlatformApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.old_data = os.environ.get("RESEARCH_OS_DATA_DIR")
        self.old_secret = os.environ.get("RESEARCH_OS_IDENTITY_PROXY_SECRET")
        os.environ["RESEARCH_OS_DATA_DIR"] = self.temp.name
        os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = "test-gateway-secret"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DeveloperPlatformHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        if self.old_data is None:
            os.environ.pop("RESEARCH_OS_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_DATA_DIR"] = self.old_data
        if self.old_secret is None:
            os.environ.pop("RESEARCH_OS_IDENTITY_PROXY_SECRET", None)
        else:
            os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = self.old_secret
        self.temp.cleanup()

    def request(self, method: str, path: str, principal: str | None, body: dict | None = None, secret: str = "test-gateway-secret"):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        headers = {"Content-Type": "application/json"}
        if principal is not None:
            headers["X-ResearchOS-Principal"] = principal
            headers["X-ResearchOS-Identity-Secret"] = secret
        payload = json.dumps(body or {}) if body is not None else None
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        status = response.status
        conn.close()
        return status, data

    def test_trial_mode_requires_no_registration_or_identity(self) -> None:
        status, payload = self.request("GET", "/v2/developer/trial", None)
        self.assertEqual(status, 200)
        self.assertEqual(payload["mode"], "trial")
        self.assertFalse(payload["registration_required"])
        self.assertFalse(payload["persistent_account"])
        self.assertEqual(payload["data_source"], "synthetic_demo_only")
        self.assertIn("write", payload["restricted"])
        self.assertIn("real_file_access", payload["restricted"])

    def test_trial_resources_are_synthetic_and_read_only(self) -> None:
        status, listing = self.request("GET", "/v2/developer/trial/resources?q=python", None)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(listing["count"], 1)
        resource_id = listing["items"][0]["resource_id"]
        self.assertNotIn("content", listing["items"][0])

        status, resource = self.request("GET", f"/v2/developer/trial/resources/{resource_id}", None)
        self.assertEqual(status, 200)
        self.assertTrue(resource["read_only"])
        self.assertEqual(resource["resource"]["workspace_id"], "trial-workspace")
        self.assertIn("content", resource["resource"])

        status, authorization = self.request(
            "POST",
            "/v2/developer/trial/authorize",
            None,
            {"resource_id": resource_id, "scope": "read"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(authorization["authorization"]["allowed"])
        self.assertFalse(authorization["authorization"]["persistent"])
        self.assertFalse(authorization["authorization"]["real_resource"])

    def test_trial_mode_rejects_write_and_management_actions(self) -> None:
        for path, body in (
            ("/v2/developer/trial/authorize", {"resource_id": "demo-api-client", "scope": "write"}),
            ("/v2/developer/trial/commit", {"message": "change"}),
            ("/v2/developer/trial/approve", {"request_id": "anything"}),
        ):
            status, payload = self.request("POST", path, None, body)
            self.assertEqual(status, 403)
            self.assertEqual(payload["error"]["code"], "trial_restricted")

    def test_trial_mode_does_not_create_access_metadata(self) -> None:
        self.request("GET", "/v2/developer/trial/resources", None)
        self.request(
            "POST",
            "/v2/developer/trial/authorize",
            None,
            {"resource_id": "demo-api-client", "scope": "read"},
        )
        developer_dir = os.path.join(self.temp.name, "developer-access")
        self.assertFalse(os.path.exists(developer_dir))

    def test_untrusted_identity_is_rejected(self) -> None:
        status, payload = self.request("GET", "/v2/developer/grants", "dev:alice", secret="wrong")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"]["code"], "identity_required")

    def test_owner_approval_flow_keeps_owner_access_unchanged(self) -> None:
        status, payload = self.request(
            "POST",
            "/v2/developer/access-requests",
            "dev:alice",
            {
                "owner_id": "user:owner",
                "workspace_id": "workspace-1",
                "resource_id": "file-1",
                "resource_name": "Owner file.md",
                "scopes": ["read", "write"],
                "purpose": "Implement an approved fix",
            },
        )
        self.assertEqual(status, 201)
        self.assertFalse(payload["access_active"])
        request_id = payload["request"]["request_id"]

        status, before = self.request(
            "POST",
            "/v2/developer/authorize",
            "dev:alice",
            {"owner_id": "user:owner", "workspace_id": "workspace-1", "resource_id": "file-1", "scope": "read"},
        )
        self.assertEqual(status, 200)
        self.assertFalse(before["authorization"]["allowed"])

        status, approved = self.request(
            "POST",
            f"/v2/developer/access-requests/{request_id}/approve",
            "user:owner",
            {"scopes": ["read"], "expires_in_seconds": 3600},
        )
        self.assertEqual(status, 200)
        grant = approved["grant"]
        self.assertTrue(grant["owner_access_unchanged"])

        status, read = self.request(
            "POST",
            "/v2/developer/authorize",
            "dev:alice",
            {"owner_id": "user:owner", "workspace_id": "workspace-1", "resource_id": "file-1", "scope": "read"},
        )
        self.assertTrue(read["authorization"]["allowed"])

        status, write = self.request(
            "POST",
            "/v2/developer/authorize",
            "dev:alice",
            {"owner_id": "user:owner", "workspace_id": "workspace-1", "resource_id": "file-1", "scope": "write"},
        )
        self.assertFalse(write["authorization"]["allowed"])

        status, owner = self.request(
            "POST",
            "/v2/developer/authorize",
            "user:owner",
            {"owner_id": "user:owner", "workspace_id": "workspace-1", "resource_id": "file-1", "scope": "write"},
        )
        self.assertTrue(owner["authorization"]["allowed"])
        self.assertEqual(owner["authorization"]["mode"], "owner")

        status, revoked = self.request(
            "POST",
            f"/v2/developer/grants/{grant['grant_id']}/revoke",
            "user:owner",
            {"reason": "Developer task complete"},
        )
        self.assertEqual(status, 200)
        self.assertFalse(revoked["grant"]["active"])

        _, after = self.request(
            "POST",
            "/v2/developer/authorize",
            "dev:alice",
            {"owner_id": "user:owner", "workspace_id": "workspace-1", "resource_id": "file-1", "scope": "read"},
        )
        self.assertFalse(after["authorization"]["allowed"])

    def test_non_owner_cannot_approve(self) -> None:
        _, payload = self.request(
            "POST",
            "/v2/developer/access-requests",
            "dev:alice",
            {
                "owner_id": "user:owner",
                "workspace_id": "workspace-1",
                "resource_id": "file-2",
                "resource_name": "Owner file 2.md",
                "scopes": ["read"],
                "purpose": "Review",
            },
        )
        request_id = payload["request"]["request_id"]
        status, denied = self.request(
            "POST",
            f"/v2/developer/access-requests/{request_id}/approve",
            "user:not-owner",
            {"scopes": ["read"]},
        )
        self.assertEqual(status, 403)
        self.assertEqual(denied["error"]["code"], "permission_denied")


if __name__ == "__main__":
    unittest.main()
