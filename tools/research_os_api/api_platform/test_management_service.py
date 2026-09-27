import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools.research_os_api.api_platform.management_http import ManagementHTTP
from tools.research_os_api.api_platform.management_service import JsonManagementStore, ManagementService


class ManagementServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("RESEARCH_OS_API_KEY_PEPPER", "test-only-pepper")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = ManagementService(JsonManagementStore(Path(self.temp.name) / "management.json"))

    def tearDown(self):
        self.temp.cleanup()

    def test_full_metadata_hierarchy_is_durable(self):
        self.service.create("organizations", {"organization_id": "org-1", "name": "Research"})
        self.service.create("projects", {"project_id": "proj-1", "organization_id": "org-1", "name": "Platform"})
        self.service.create("applications", {"application_id": "app-1", "project_id": "proj-1", "name": "Console"})
        self.service.create("apis", {"api_id": "api-1", "project_id": "proj-1", "name": "Research API"})
        self.service.create("versions", {"version_id": "ver-1", "api_id": "api-1", "version": "1.0"})
        self.service.create("scopes", {"scope_id": "scope:read", "name": "scope:read"})
        self.service.create("endpoints", {"endpoint_id": "ep-1", "version_id": "ver-1", "method": "GET", "path": "/health", "operation_id": "health", "scopes": ["scope:read"]})
        self.service.create("plans", {"plan_id": "plan-1", "project_id": "proj-1", "name": "default"})
        self.service.create("entitlements", {"entitlement_id": "ent-1", "plan_id": "plan-1", "scope_ids": ["scope:read"]})
        self.service.create("routes", {"route_id": "route-1", "endpoint_id": "ep-1", "target": "runtime"})
        self.service.create("webhooks", {"webhook_id": "hook-1", "project_id": "proj-1", "url": "https://example.test/hook", "event_types": ["api.published"]})
        self.service.create("products", {"product_id": "product-1", "project_id": "proj-1", "name": "Core", "api_ids": ["api-1"], "plan_ids": ["plan-1"]})
        self.service.create("portals", {"project_id": "proj-1", "title": "Developer Portal", "sdk_languages": ["python"]})
        reopened = ManagementService(self.service.store)
        self.assertEqual(reopened.get("projects", "proj-1")["name"], "Platform")
        self.assertEqual(reopened.get("endpoints", "ep-1")["scopes"], ["scope:read"])

    def test_invalid_relationship_fails_closed(self):
        self.service.create("organizations", {"organization_id": "org-1", "name": "Research"})
        with self.assertRaises(ValueError):
            self.service.create("projects", {"project_id": "proj-1", "organization_id": "missing", "name": "Bad"})

    def test_lifecycle_is_metadata_only(self):
        self.service.create("organizations", {"organization_id": "org-1", "name": "Research"})
        self.service.create("projects", {"project_id": "proj-1", "organization_id": "org-1", "name": "Platform"})
        self.service.create("apis", {"api_id": "api-1", "project_id": "proj-1", "name": "Research API"})
        updated = self.service.lifecycle("apis", "api-1", "disable")
        self.assertEqual(updated["lifecycle"], "disabled")

    def test_api_key_scope_is_bound_to_entitlement(self):
        self.service.create("organizations", {"organization_id": "org-1", "name": "Research"})
        self.service.create("projects", {"project_id": "proj-1", "organization_id": "org-1", "name": "Platform"})
        self.service.create("applications", {"application_id": "app-1", "project_id": "proj-1", "name": "Console"})
        self.service.create("scopes", {"scope_id": "scope:read", "name": "scope:read"})
        self.service.create("scopes", {"scope_id": "scope:write", "name": "scope:write"})
        self.service.create("plans", {"plan_id": "plan-1", "project_id": "proj-1", "name": "default"})
        self.service.create("entitlements", {"entitlement_id": "ent-1", "plan_id": "plan-1", "scope_ids": ["scope:read"]})
        with self.assertRaises(ValueError):
            self.service.create_api_key({"application_id": "app-1", "principal_id": "principal-1", "entitlement_id": "ent-1", "scopes": ["scope:write"]})
        result = self.service.create_api_key({"application_id": "app-1", "principal_id": "principal-1", "entitlement_id": "ent-1", "scopes": ["scope:read"]})
        self.assertEqual(result["entitlement_id"], "ent-1")
        self.assertIn("raw_secret", result)

    def test_http_auth_and_crud(self):
        http = ManagementHTTP(self.service, lambda headers: {"user_id": "owner"} if headers.get("X-Test-Auth") else None)
        status, _ = http.dispatch("GET", "/platform/v1/projects", {}, None)
        self.assertEqual(status, 401)
        status, body = http.dispatch("POST", "/platform/v1/organizations", {"X-Test-Auth": "1"}, {"organization_id": "org-1", "name": "Research"})
        self.assertEqual(status, 201)
        self.assertEqual(body["organization_id"], "org-1")
        status, body = http.dispatch("GET", "/platform/v1/organizations", {"X-Test-Auth": "1"}, None)
        self.assertEqual(status, 200)
        self.assertEqual(body["count"], 1)

    def test_audit_is_append_only(self):
        self.service.create("organizations", {"organization_id": "org-1", "name": "Research"}, actor="owner")
        audit = self.service.store.audit()
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]["action"], "create")
        self.assertEqual(audit[0]["actor"], "owner")


if __name__ == "__main__":
    unittest.main()
