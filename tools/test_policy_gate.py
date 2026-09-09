from __future__ import annotations

import json
import unittest
from pathlib import Path

from compile_policy_gate import compile_policy
from evaluate_policy_gate import evaluate

ROOT = Path(__file__).resolve().parents[1]


class PolicyGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads((ROOT / "current" / "POLICY_GATE_FIXTURE.json").read_text(encoding="utf-8"))
        cls.plan = compile_policy(cls.policy)

    def complete_evidence(self) -> dict[str, str]:
        return {
            "identity_verified": "VERIFIED",
            "capability_verified": "VERIFIED",
            "authorization_proof": "VERIFIED",
            "provenance_verified": "VERIFIED",
            "scope_verified": "VERIFIED",
            "revocation_verified": "VERIFIED",
            "delegation_verified": "VERIFIED",
        }

    def test_valid_policy_passes(self) -> None:
        receipt = evaluate(self.plan, self.complete_evidence())
        self.assertEqual(receipt["decision"], "PASS")
        self.assertTrue(receipt["evaluation_fingerprint"])

    def test_missing_evidence_blocks(self) -> None:
        evidence = self.complete_evidence()
        del evidence["authorization_proof"]
        receipt = evaluate(self.plan, evidence)
        self.assertEqual(receipt["decision"], "BLOCK")
        self.assertIn("authorization_proof:MISSING", receipt["reason_codes"])

    def test_unknown_evidence_blocks(self) -> None:
        evidence = self.complete_evidence()
        evidence["provenance_verified"] = "UNKNOWN"
        receipt = evaluate(self.plan, evidence)
        self.assertEqual(receipt["decision"], "BLOCK")

    def test_stale_evidence_blocks(self) -> None:
        evidence = self.complete_evidence()
        evidence["scope_verified"] = "STALE"
        receipt = evaluate(self.plan, evidence)
        self.assertEqual(receipt["decision"], "BLOCK")

    def test_revoked_authority_blocks(self) -> None:
        evidence = self.complete_evidence()
        evidence["revocation_verified"] = "REJECTED"
        receipt = evaluate(self.plan, evidence)
        self.assertEqual(receipt["decision"], "BLOCK")

    def test_scope_escalation_blocks(self) -> None:
        evidence = self.complete_evidence()
        evidence["scope_verified"] = "REJECTED"
        receipt = evaluate(self.plan, evidence)
        self.assertEqual(receipt["decision"], "BLOCK")

    def test_deterministic_fingerprint_excludes_clock(self) -> None:
        evidence = self.complete_evidence()
        first = evaluate(self.plan, evidence)
        second = evaluate(self.plan, evidence)
        self.assertEqual(first["decision"], second["decision"])
        self.assertEqual(first["evaluation_fingerprint"], second["evaluation_fingerprint"])

    def test_compiler_rejects_tampered_policy_fingerprint(self) -> None:
        tampered = dict(self.policy)
        tampered["policy_fingerprint"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "invalid_policy_fingerprint"):
            compile_policy(tampered)

    def test_compiler_cannot_grant_authority(self) -> None:
        self.assertEqual(self.plan["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
