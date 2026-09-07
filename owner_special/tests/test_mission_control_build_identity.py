from __future__ import annotations

import copy
import unittest

from owner_special.research_os_friend.mission_control_build_identity import (
    MissionControlBuildIdentityError,
    MissionControlBuildIdentityProjection,
)


BUILD = {
    "gate": "owner-special-build-identity",
    "passed": True,
    "file_name": "research_os_owner_special.exe",
    "sha256": "A" * 64,
    "product_name": "research_os_owner_special",
    "internal_name": "research_os_owner_special",
    "original_filename": "research_os_owner_special.exe",
    "file_description": "research_os_owner_special",
    "company_name": "com.example",
    "owner_edition": "owner-special",
    "owner_only": True,
    "manifest_version": "1",
    "commit": "ABCDEF1234567890",
}

INSTALLED = {
    "passed": True,
    "owner_edition": "owner-special",
    "file_name": "research_os_owner_special.exe",
    "sha256": "a" * 64,
    "commit": "abcdef1234567890",
}


class MissionControlBuildIdentityProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.projection = MissionControlBuildIdentityProjection()

    def test_verified_identity_requires_matching_canonical_evidence(self):
        result = self.projection.snapshot(
            owner_id="owner-special",
            build_identity=BUILD,
            installed_provenance=INSTALLED,
            expected_commit="abcdef1234567890",
        )
        self.assertEqual(result["status"], "VERIFIED")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["identity"]["file_name"], "research_os_owner_special.exe")

    def test_missing_provenance_fails_closed(self):
        result = self.projection.snapshot(owner_id="owner-special", build_identity=BUILD, installed_provenance=None)
        self.assertEqual(result["status"], "PENDING")

    def test_conflicting_sha_is_rejected(self):
        installed = dict(INSTALLED, sha256="b" * 64)
        result = self.projection.snapshot(owner_id="owner-special", build_identity=BUILD, installed_provenance=installed)
        self.assertEqual(result["status"], "CONFLICT")

    def test_stale_commit_is_rejected(self):
        result = self.projection.snapshot(
            owner_id="owner-special",
            build_identity=BUILD,
            installed_provenance=INSTALLED,
            expected_commit="different-commit",
        )
        self.assertEqual(result["status"], "STALE")

    def test_deterministic_output(self):
        first = self.projection.snapshot(owner_id="owner-special", build_identity=BUILD, installed_provenance=INSTALLED)
        second = self.projection.snapshot(owner_id="owner-special", build_identity=BUILD, installed_provenance=INSTALLED)
        self.assertEqual(first, second)

    def test_input_is_immutable(self):
        build = copy.deepcopy(BUILD)
        installed = copy.deepcopy(INSTALLED)
        self.projection.snapshot(owner_id="owner-special", build_identity=build, installed_provenance=installed)
        self.assertEqual(build, BUILD)
        self.assertEqual(installed, INSTALLED)

    def test_secret_like_source_value_is_rejected(self):
        build = dict(BUILD, product_name="api_key=should-never-be-projected")
        with self.assertRaises(MissionControlBuildIdentityError):
            self.projection.snapshot(owner_id="owner-special", build_identity=build, installed_provenance=INSTALLED)

    def test_filename_alone_never_verifies(self):
        build = {"file_name": "research_os_owner_special.exe", "passed": True}
        installed = {"file_name": "research_os_owner_special.exe", "passed": True}
        result = self.projection.snapshot(owner_id="owner-special", build_identity=build, installed_provenance=installed)
        self.assertNotEqual(result["status"], "VERIFIED")

    def test_oversized_owner_is_rejected(self):
        with self.assertRaises(MissionControlBuildIdentityError):
            self.projection.snapshot(owner_id="x" * 2049, build_identity=BUILD, installed_provenance=INSTALLED)

    def test_no_action_authority_is_projected(self):
        result = self.projection.snapshot(owner_id="owner-special", build_identity=BUILD, installed_provenance=INSTALLED)
        self.assertNotIn("execute", result)
        self.assertNotIn("approve", result)
        self.assertNotIn("install", result)
        self.assertNotIn("dispatch", result)


if __name__ == "__main__":
    unittest.main()
