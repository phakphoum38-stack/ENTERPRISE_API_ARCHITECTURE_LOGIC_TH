import unittest

from owner_special.research_os_friend.mission_control_ui_schema import (
    MissionControlUISchemaError,
    MissionControlUISchemaValidator,
)


class MissionControlUISchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = MissionControlUISchemaValidator()

    def payload(self):
        return {
            "schema": "research-os-mission-control-ui/v1",
            "owner_id": "owner-1",
            "read_only": True,
            "execution_authority": "FriendOrchestrator",
            "authorization_authority": "OwnerPolicy",
            "approval_authority": "ApprovalGate",
            "panels": [
                {"id": "health", "type": "status", "title": "Health", "value": "ready"},
                {"id": "summary", "type": "text", "title": "Summary", "value": "All bounded."},
            ],
        }

    def test_valid_payload_is_accepted_and_copied(self):
        payload = self.payload()
        result = self.validator.validate(payload, owner_id="owner-1")
        self.assertEqual(result, payload)
        self.assertIsNot(result, payload)
        result["panels"].append({"id": "z", "type": "text"})
        self.assertEqual(len(payload["panels"]), 2)

    def test_schema_read_only_owner_and_authorities_are_strict(self):
        for field, value in (("schema", "v2"), ("read_only", False), ("owner_id", "owner-2"), ("approval_authority", "Other")):
            payload = self.payload()
            payload[field] = value
            with self.assertRaises(MissionControlUISchemaError):
                self.validator.validate(payload, owner_id="owner-1")

    def test_unknown_panel_and_unknown_root_field_fail(self):
        payload = self.payload()
        payload["panels"][0]["type"] = "custom-widget"
        with self.assertRaises(MissionControlUISchemaError):
            self.validator.validate(payload, owner_id="owner-1")

        payload = self.payload()
        payload["unknown"] = "x"
        with self.assertRaises(MissionControlUISchemaError):
            self.validator.validate(payload, owner_id="owner-1")

    def test_malicious_dynamic_and_execution_descriptors_fail(self):
        for key, value in (
            ("callback", "run()"),
            ("handler", "process.start"),
            ("command", "powershell -Command whoami"),
            ("mcp_execute", "true"),
            ("credential", "Bearer abc"),
        ):
            payload = self.payload()
            payload["panels"][0][key] = value
            with self.assertRaises(MissionControlUISchemaError):
                self.validator.validate(payload, owner_id="owner-1")

    def test_bounds_and_deterministic_order_fail_closed(self):
        payload = self.payload()
        payload["panels"] = list(reversed(payload["panels"]))
        with self.assertRaises(MissionControlUISchemaError):
            self.validator.validate(payload, owner_id="owner-1")

        payload = self.payload()
        payload["panels"] = [
            {"id": str(i), "type": "text", "value": "x"} for i in range(self.validator.MAX_PANELS + 1)
        ]
        with self.assertRaises(MissionControlUISchemaError):
            self.validator.validate(payload, owner_id="owner-1")

        payload = self.payload()
        payload["panels"][0]["items"] = ["x"] * (self.validator.MAX_ITEMS + 1)
        with self.assertRaises(MissionControlUISchemaError):
            self.validator.validate(payload, owner_id="owner-1")

    def test_dynamic_objects_and_oversized_bytes_fail(self):
        payload = self.payload()
        payload["panels"][0]["value"] = object()
        with self.assertRaises(MissionControlUISchemaError):
            self.validator.validate(payload, owner_id="owner-1")

        with self.assertRaises(MissionControlUISchemaError):
            self.validator.validate_json_size(b"x" * (self.validator.MAX_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
