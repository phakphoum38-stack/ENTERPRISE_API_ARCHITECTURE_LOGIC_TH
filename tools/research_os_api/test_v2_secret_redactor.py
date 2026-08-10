#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_secret_redactor import (
    SECRET_REDACTION_CONTRACT,
    current_secret_values,
    discover_secret_values,
    redaction_status,
    sanitize_external,
    secret_scope,
)


class SecretRedactorTests(unittest.TestCase):
    def test_discovers_sensitive_field_values_without_persisting_metadata(self) -> None:
        secrets = discover_secret_values(
            {"api_key": "alpha-secret-12345", "nested": {"password": "beta-secret-67890"}},
            explicit=("explicit-secret-99999",),
        )
        self.assertEqual(
            {"alpha-secret-12345", "beta-secret-67890", "explicit-secret-99999"},
            set(secrets),
        )
        report = redaction_status()
        self.assertEqual(SECRET_REDACTION_CONTRACT, report["contract"])
        self.assertFalse(report["secret_values_persisted"])

    def test_value_aware_redaction_scrubs_reflected_secret_under_innocent_key(self) -> None:
        secret = "value-secret-123456789"
        safe = sanitize_external(
            {"message": f"adapter reflected {secret}", "status": "ok"},
            secret_values=(secret,),
        )
        self.assertNotIn(secret, repr(safe))
        self.assertIn("[REDACTED]", safe["message"])

    def test_common_bearer_and_provider_key_shapes_are_scrubbed(self) -> None:
        safe = sanitize_external(
            {
                "message": "Bearer abcdefghijklmnop",
                "provider": "sk-abcdefghijklmnopqrstuvwxyz",
            },
            secret_values=(),
        )
        self.assertNotIn("abcdefghijklmnop", repr(safe))
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz", repr(safe))

    def test_secret_scope_is_context_local_and_restored(self) -> None:
        self.assertEqual((), current_secret_values())
        with secret_scope(("scoped-secret-12345",)):
            self.assertEqual(("scoped-secret-12345",), current_secret_values())
            safe = sanitize_external({"message": "scoped-secret-12345"})
            self.assertEqual("[REDACTED]", safe["message"])
        self.assertEqual((), current_secret_values())


if __name__ == "__main__":
    unittest.main()
