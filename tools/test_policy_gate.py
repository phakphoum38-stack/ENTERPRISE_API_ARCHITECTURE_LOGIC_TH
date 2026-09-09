from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.compile_policy_gate import compile_policy
from tools.evaluate_policy_gate import evaluate

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
            "human_approval": "VERIFIED",
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

    def test_high_risk_without_approval_requires_approval(self) -> None:
        evidence = self.complete_evidence()
        del evidence["human_approval"]
        receipt = evaluate(self.plan, evidence)
        self.assertEqual(receipt["decision"], "REQUIRE_APPROVAL")
        self.assertIn("human_approval:PENDING", receipt["reason_codes"])

    def test_rejected_approval_blocks(self) -> None:
        evidence = self.complete_evidence()
        evidence["human_approval"] = "REJECTED"
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

    def test_compiler_rejects_high_risk_without_approval(self) -> None:
        tampered = json.loads(json.dumps(self.policy))
        tampered["rules"][0]["approval_mode"] = "NONE"
        from tools.compile_policy_gate import policy_fingerprint
        tampered["policy_fingerprint"] = policy_fingerprint(tampered)
        with self.assertRaisesRegex(ValueError, "high_risk_requires_approval"):
            compile_policy(tampered)

    def test_compiler_cannot_grant_authority(self) -> None:
        self.assertEqual(self.plan["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
