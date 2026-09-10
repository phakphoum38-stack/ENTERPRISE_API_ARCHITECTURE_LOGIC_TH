#!/usr/bin/env python3
"""Negative and differential tests for AEOS Master Assurance semantics."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.aeos_master_assurance import ControlResult, failure_event_id, failure_signature, verify_fix
from tools.validate_aeos_manifest import validate_manifest


CONTROL_ID = "SYNTHETIC_CONTROL"
CLASS_NAME = "negative_assurance"
COMMAND = ["python", "-c", "raise SystemExit(1)"]
OLD_SHA = "1" * 40
NEW_SHA = "2" * 40


def _result(*, status: str, detail: str = "known_failure") -> ControlResult:
    returncode = 1 if status != "PASS" else 0
    return ControlResult(
        control_id=CONTROL_ID,
        class_name=CLASS_NAME,
        status=status,
        command=COMMAND,
        cwd=".",
        returncode=returncode,
        duration_seconds=0.001,
        detail=detail,
        evidence_id=failure_event_id(CONTROL_ID, returncode, detail),
        failure_signature=(
            failure_signature(CONTROL_ID, CLASS_NAME, COMMAND, detail)
            if status != "PASS"
            else None
        ),
    )


def _previous(*results: ControlResult) -> dict[str, object]:
    controls = [result.__dict__.copy() for result in results]
    return {
        "schema": "AEOS_MASTER_ASSURANCE_V2",
        "source_sha": OLD_SHA,
        "controls": controls,
        "control_count": len(controls),
        "decision": "FAIL" if any(r.status != "PASS" for r in results) else "PASS",
        "passed": sum(r.status == "PASS" for r in results),
        "failed": sum(r.status != "PASS" for r in results),
    }


class TestAeosDifferentialAssurance(unittest.TestCase):
    def test_resolved_old_failure_passes(self) -> None:
        old = _previous(_result(status="FAIL"))
        new = [_result(status="PASS")]
        with patch("tools.aeos_master_assurance.git_sha", return_value=NEW_SHA):
            result = verify_fix(new, old)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["resolved_failures"]), 1)
        self.assertEqual(result["regressions"], [])

    def test_persistent_old_failure_fails_closed(self) -> None:
        old = _previous(_result(status="FAIL"))
        new = [_result(status="FAIL")]
        with patch("tools.aeos_master_assurance.git_sha", return_value=NEW_SHA):
            result = verify_fix(new, old)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["unresolved_failures"], result["old_failure_signatures"])

    def test_new_failure_is_regression(self) -> None:
        old = _previous(_result(status="FAIL", detail="old_failure"))
        new = [_result(status="FAIL", detail="new_failure")]
        with patch("tools.aeos_master_assurance.git_sha", return_value=NEW_SHA):
            result = verify_fix(new, old)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["regressions"])

    def test_missing_old_control_is_failure(self) -> None:
        old = _previous(_result(status="PASS"))
        new = []
        with patch("tools.aeos_master_assurance.git_sha", return_value=NEW_SHA):
            result = verify_fix(new, old)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["missing_controls"], [CONTROL_ID])

    def test_no_old_failures_is_insufficient_evidence(self) -> None:
        old = _previous(_result(status="PASS"))
        new = [_result(status="PASS")]
        with patch("tools.aeos_master_assurance.git_sha", return_value=NEW_SHA):
            result = verify_fix(new, old)
        self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")


class TestAeosEvidenceIdentity(unittest.TestCase):
    def test_event_id_is_bound_to_exact_payload(self) -> None:
        detail = "known_failure"
        expected = hashlib.sha256(f"{CONTROL_ID}|1|{detail}".encode("utf-8")).hexdigest()
        self.assertEqual(failure_event_id(CONTROL_ID, 1, detail), expected)
        self.assertNotEqual(failure_event_id(CONTROL_ID, 1, "changed_failure"), expected)
        self.assertNotEqual(failure_event_id("OTHER_CONTROL", 1, detail), expected)


class TestAeosManifestTamperDefense(unittest.TestCase):
    def _manifest(self, directory: Path) -> tuple[Path, Path]:
        manifest = directory / "previous.json"
        detail = "known_failure"
        payload = {
            "schema": "AEOS_MASTER_ASSURANCE_V2",
            "source_sha": OLD_SHA,
            "controls": [
                {
                    "control_id": CONTROL_ID,
                    "class_name": CLASS_NAME,
                    "status": "FAIL",
                    "command": COMMAND,
                    "cwd": ".",
                    "returncode": 1,
                    "duration_seconds": 0.001,
                    "detail": detail,
                    "evidence_id": failure_event_id(CONTROL_ID, 1, detail),
                    "failure_signature": failure_signature(CONTROL_ID, CLASS_NAME, COMMAND, detail),
                }
            ],
            "control_count": 1,
            "passed": 0,
            "failed": 1,
            "decision": "FAIL",
            "fix_verification": {"status": "NOT_REQUESTED"},
        }
        manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        sidecar = Path(str(manifest) + ".sha256")
        sidecar.write_text(f"{digest}  {manifest.name}\n", encoding="utf-8")
        return manifest, sidecar

    def test_tampered_manifest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest, sidecar = self._manifest(Path(temp))
            original = manifest.read_text(encoding="utf-8")
            manifest.write_text(original.replace("known_failure", "tampered_failure"), encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                with patch("tools.validate_aeos_manifest._git_commit_exists", return_value=True), patch(
                    "tools.validate_aeos_manifest._git_is_ancestor", return_value=True
                ):
                    validate_manifest(manifest, repo=Path(temp), require_commit=True)
            self.assertIn("manifest_digest_mismatch", str(raised.exception))

    def test_tampered_sidecar_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest, sidecar = self._manifest(Path(temp))
            sidecar.write_text(f"{'0' * 64}  {manifest.name}\n", encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                with patch("tools.validate_aeos_manifest._git_commit_exists", return_value=True), patch(
                    "tools.validate_aeos_manifest._git_is_ancestor", return_value=True
                ):
                    validate_manifest(manifest, repo=Path(temp), require_commit=True)
            self.assertIn("manifest_digest_mismatch", str(raised.exception))

    def test_tampered_evidence_id_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest, _ = self._manifest(Path(temp))
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["controls"][0]["evidence_id"] = "0" * 64
            manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
            Path(str(manifest) + ".sha256").write_text(f"{digest}  {manifest.name}\n", encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                with patch("tools.validate_aeos_manifest._git_commit_exists", return_value=True), patch(
                    "tools.validate_aeos_manifest._git_is_ancestor", return_value=True
                ):
                    validate_manifest(manifest, repo=Path(temp), require_commit=True)
            self.assertIn("evidence_id_mismatch", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
