#!/usr/bin/env python3
"""Metamorphic assurance tests for stable AEOS failure identity."""
from __future__ import annotations

import unittest

from tools.aeos_master_assurance import failure_signature


CONTROL_ID = "SYNTHETIC_CONTROL"
CLASS_NAME = "negative_assurance"
COMMAND = ["python", "-c", "raise SystemExit(1)"]


class TestAeosFailureIdentity(unittest.TestCase):
    def test_runtime_identifiers_do_not_change_recurrence_signature(self) -> None:
        base = "validation failed run=aeos-123-456 sha=0123456789abcdef0123456789abcdef01234567 duration=0.1s line=42"
        changed = "validation failed run=aeos-987-654 sha=fedcba9876543210fedcba9876543210fedcba98 duration=9.9s line=999"
        self.assertEqual(
            failure_signature(CONTROL_ID, CLASS_NAME, COMMAND, base),
            failure_signature(CONTROL_ID, CLASS_NAME, COMMAND, changed),
        )

    def test_semantic_failure_change_changes_recurrence_signature(self) -> None:
        old = "validation failed: missing contract symbol"
        new = "validation failed: missing required provenance binding"
        self.assertNotEqual(
            failure_signature(CONTROL_ID, CLASS_NAME, COMMAND, old),
            failure_signature(CONTROL_ID, CLASS_NAME, COMMAND, new),
        )

    def test_control_identity_is_part_of_recurrence_signature(self) -> None:
        detail = "validation failed: missing contract symbol"
        first = failure_signature("CONTROL_A", CLASS_NAME, COMMAND, detail)
        second = failure_signature("CONTROL_B", CLASS_NAME, COMMAND, detail)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
