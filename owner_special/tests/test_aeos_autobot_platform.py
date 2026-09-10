#!/usr/bin/env python3
"""Negative assurance for AEOS Autobot platform authority and bounds."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.aeos_autobot_platform import _validate_registry, run_platform


class PlatformContractTests(unittest.TestCase):
    def canonical(self, *entries: dict) -> dict:
        return {
            "contract": "AEOS_AUTOBOT_ASSURANCE_SET_REGISTRY",
            "set_count": len(entries),
            "sets": list(entries),
        }

    def projection(self, *entries: dict) -> dict:
        return {"max_sets": 100, "sets": list(entries)}

    def test_canonical_registry_is_authoritative(self) -> None:
        canonical = self.canonical({"set_id": "SET-001", "name": "A", "wave": "W0", "status": "IMPLEMENTED"})
        projection = self.projection({
            "set_id": "SET-001", "name": "B", "wave": "IDENTITY", "status": "active",
            "command": "python -c pass", "cwd": ".", "source_sha_policy": "HEAD",
            "timeout_seconds": 10, "allowed_exit_codes": [0], "evidence_policy": "required",
            "repair_policy": "none", "scope": 1, "changed_files": 0, "risk_level": 1,
        })
        with self.assertRaisesRegex(ValueError, "canonical_name_mismatch"):
            _validate_registry(projection, canonical)

    def test_implemented_set_cannot_be_omitted_from_projection(self) -> None:
        canonical = self.canonical({"set_id": "SET-001", "name": "A", "wave": "W0", "status": "IMPLEMENTED"})
        with self.assertRaisesRegex(ValueError, "canonical_required_set_missing"):
            _validate_registry(self.projection(), canonical)

    def test_implemented_set_requires_executable_safety_metadata(self) -> None:
        canonical = self.canonical({"set_id": "SET-001", "name": "A", "wave": "W0", "status": "IMPLEMENTED"})
        projection = self.projection({"set_id": "SET-001", "name": "A", "wave": "IDENTITY", "status": "active"})
        with self.assertRaisesRegex(ValueError, "active_set_metadata_missing"):
            _validate_registry(projection, canonical)

    def test_canonical_wave_is_bound_to_projection_wave(self) -> None:
        canonical = self.canonical({"set_id": "SET-001", "name": "A", "wave": "W0", "status": "IMPLEMENTED"})
        projection = self.projection({
            "set_id": "SET-001", "name": "A", "wave": "SOURCE_CONTRACT", "status": "active",
            "command": "python -c pass", "cwd": ".", "source_sha_policy": "HEAD",
            "timeout_seconds": 10, "allowed_exit_codes": [0], "evidence_policy": "required",
            "repair_policy": "none", "scope": 1, "changed_files": 0, "risk_level": 1,
        })
        with self.assertRaisesRegex(ValueError, "canonical_wave_mismatch"):
            _validate_registry(projection, canonical)

    def test_global_runtime_limit_is_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "registry.json"
            canonical = Path(tmp) / "canonical.json"
            output = Path(tmp) / "manifest.json"
            registry.write_text(json.dumps(self.projection()), encoding="utf-8")
            canonical.write_text(json.dumps(self.canonical()), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid_execution_limits"):
                run_platform(registry, output, 1, canonical_registry_path=canonical, max_runtime_seconds=0)

    def test_owner_authority_decision_is_not_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "registry.json"
            canonical = Path(tmp) / "canonical.json"
            output = Path(tmp) / "manifest.json"
            entry = {
                "set_id": "SET-001", "name": "A", "wave": "W0", "status": "active",
                "command": "python -c pass", "cwd": tmp, "source_sha_policy": "HEAD",
                "timeout_seconds": 10, "allowed_exit_codes": [0], "evidence_policy": "required",
                "repair_policy": "none", "scope": 1, "changed_files": 0, "risk_level": 1,
            }
            registry.write_text(json.dumps(self.projection(entry)), encoding="utf-8")
            canonical.write_text(json.dumps(self.canonical({"set_id": "SET-001", "name": "A", "wave": "W0", "status": "IMPLEMENTED"})), encoding="utf-8")
            with patch("tools.aeos_autobot_platform._git_sha", return_value="a" * 40), \
                 patch("tools.aeos_autobot_platform.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = ""
                result = run_platform(registry, output, 1, canonical_registry_path=canonical, max_runtime_seconds=30)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(manifest["decision"], "READY_FOR_OWNER_AUTHORITY")
            self.assertEqual(manifest["authority"], "OWNER_ONLY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
