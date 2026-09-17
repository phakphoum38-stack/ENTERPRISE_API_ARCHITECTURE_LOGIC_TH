import unittest
from datetime import datetime, timezone

from api_management_models import (
    API,
    APIEndpoint,
    APIKey,
    APIVersion,
    Application,
    ManagementInvariantViolation,
    Organization,
    Plan,
    Project,
    Scope,
    validate_api_key_scope_subset,
    validate_management_model,
)


class APIManagementModelTests(unittest.TestCase):
    def setUp(self):
        self.org = Organization("org-1", "Research OS")
        self.project = Project("project-1", "org-1", "Demo")
        self.application = Application("app-1", "project-1", "CLI")
        self.api = API("api-1", "project-1", "Research API")
        self.version = APIVersion("version-1", "api-1", "v1")
        self.scope = Scope("scope.read", "research.read")
        self.endpoint = APIEndpoint("endpoint-1", "version-1", "GET", "/v1/research", "listResearch", ("scope.read",))

    def test_valid_relationships_pass(self):
        validate_management_model(
            organization=self.org,
            project=self.project,
            application=self.application,
            api=self.api,
            version=self.version,
            endpoint=self.endpoint,
            scopes={"scope.read": self.scope},
            plans={"plan-1": Plan("plan-1", "project-1", "Free")},
        )

    def test_cross_project_relationship_fails_closed(self):
        with self.assertRaises(ManagementInvariantViolation) as ctx:
            validate_management_model(
                organization=self.org,
                project=Project("project-2", "org-1", "Other"),
                application=self.application,
                api=self.api,
                version=self.version,
                endpoint=self.endpoint,
            )
        self.assertEqual(ctx.exception.code, "APPLICATION_PROJECT_MISMATCH")

    def test_unknown_endpoint_scope_fails_closed(self):
        with self.assertRaises(ManagementInvariantViolation) as ctx:
            validate_management_model(
                organization=self.org,
                project=self.project,
                application=self.application,
                api=self.api,
                version=self.version,
                endpoint=self.endpoint,
            )
        self.assertEqual(ctx.exception.code, "UNKNOWN_SCOPE")

    def test_invalid_endpoint_path_fails_closed(self):
        bad = APIEndpoint("endpoint-2", "version-1", "GET", "v1/research", "listResearch")
        with self.assertRaises(ManagementInvariantViolation) as ctx:
            validate_management_model(
                organization=self.org,
                project=self.project,
                application=self.application,
                api=self.api,
                version=self.version,
                endpoint=bad,
            )
        self.assertEqual(ctx.exception.code, "INVALID_ENDPOINT_PATH")

    def test_api_key_cannot_escalate_scope(self):
        key = APIKey("key-1", "app-1", "fingerprint", ("scope.read", "scope.admin"), datetime.now(timezone.utc))
        with self.assertRaises(ManagementInvariantViolation) as ctx:
            validate_api_key_scope_subset(key, ("scope.read",))
        self.assertEqual(ctx.exception.code, "API_KEY_SCOPE_ESCALATION")

    def test_api_key_within_entitlement_passes(self):
        key = APIKey("key-1", "app-1", "fingerprint", ("scope.read",), datetime.now(timezone.utc))
        validate_api_key_scope_subset(key, ("scope.read", "scope.write"))


if __name__ == "__main__":
    unittest.main()
