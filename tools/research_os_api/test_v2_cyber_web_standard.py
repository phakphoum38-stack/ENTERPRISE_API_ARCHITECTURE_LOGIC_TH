#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_cyber_web_standard import (
    CYBER_WEB_STANDARD,
    CYBER_WEB_STANDARD_CONTRACT,
)


class CyberWebSecurityStandardTests(unittest.TestCase):
    def test_manifest_uses_current_baselines_and_is_separate_from_file_ownership(self) -> None:
        manifest = CYBER_WEB_STANDARD.manifest()
        self.assertEqual(manifest["contract"], CYBER_WEB_STANDARD_CONTRACT)
        refs = {item["standard_id"]: item for item in manifest["references"]}
        self.assertEqual(refs["OWASP-ASVS"]["version"], "5.0.0")
        self.assertEqual(refs["OWASP-TOP10"]["version"], "2025")
        self.assertEqual(refs["NIST-SP-800-218"]["version"], "1.1")
        self.assertEqual(refs["NIST-SP-800-52R2"]["version"], "Rev. 2")

        boundary = manifest["boundary"]
        self.assertTrue(boundary["separate_from_file_owner_system"])
        self.assertFalse(boundary["file_owner_read_authority"])
        self.assertFalse(boundary["file_owner_write_authority"])
        self.assertFalse(boundary["file_acl_grant_authority"])
        self.assertFalse(boundary["filesystem_authorization_source"])
        self.assertFalse(manifest["permission_grant_authority"])

    def test_public_assessment_fails_closed_when_required_security_evidence_is_missing(self) -> None:
        result = CYBER_WEB_STANDARD.assess({}, deployment_mode="public")
        self.assertFalse(result["ready"])
        self.assertGreater(result["failed_required_controls"], 0)
        self.assertFalse(result["changes_file_ownership"])
        self.assertFalse(result["grants_permissions"])

    def test_public_assessment_passes_when_all_required_evidence_is_true(self) -> None:
        manifest = CYBER_WEB_STANDARD.manifest()
        evidence = {
            item["evidence_key"]: True
            for item in manifest["controls"]
            if item["required_public"]
        }
        result = CYBER_WEB_STANDARD.assess(evidence, deployment_mode="public")
        self.assertTrue(result["ready"])
        self.assertEqual(result["failed_required_controls"], 0)

    def test_loopback_mode_does_not_force_public_tls_or_hsts_controls(self) -> None:
        manifest = CYBER_WEB_STANDARD.manifest()
        evidence = {
            item["evidence_key"]: True
            for item in manifest["controls"]
            if item["required_local_loopback"]
        }
        result = CYBER_WEB_STANDARD.assess(
            evidence,
            deployment_mode="local_loopback",
        )
        self.assertTrue(result["ready"])
        by_id = {item["control_id"]: item for item in result["results"]}
        self.assertEqual(by_id["WEB-HTTPS-001"]["status"], "not_applicable")
        self.assertEqual(by_id["WEB-HSTS-011"]["status"], "not_applicable")

    def test_invalid_deployment_mode_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "deployment_mode"):
            CYBER_WEB_STANDARD.assess({}, deployment_mode="unknown")


if __name__ == "__main__":
    unittest.main()
