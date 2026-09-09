import unittest
from dataclasses import replace

from owner_special.research_os_friend.approval import ApprovalGate, ApprovalProof, ApprovalState
from owner_special.research_os_friend.identity import OwnerIdentity
from owner_special.research_os_friend.models import FriendRequest
from owner_special.research_os_friend.aeos_assurance_fabric import AssuranceControl, AssuranceFabric, AssuranceFabricError, compile_control_spec
from owner_special.research_os_friend.aeos_authority_risk import AuthorityRiskError, build_authority_verification_proof, evaluate_authority_risk
from owner_special.research_os_friend.aeos_semantic_diff import SemanticDiffError, classify_semantic_diff
from owner_special.research_os_friend.aeos_blast_radius import calculate_blast_radius
from owner_special.research_os_friend.aeos_decision_replay import DecisionReplayError, record_decision, replay_decision
from owner_special.research_os_friend.aeos_post_merge_verification import PostMergeVerificationError, verify_post_merge


SHA = "a" * 40
HASH = "b" * 64
EVIDENCE_ROOT = "c" * 64
PROVENANCE_ROOT = "d" * 64
REFS = ("EV-001", "EV-002")


def verification_proof():
    return build_authority_verification_proof(
        authority_verified=True,
        capability_verified=True,
        provenance_verified=True,
        baseline_sha=SHA,
        policy_version="p1",
        policy_sha256=HASH,
        evidence_root=EVIDENCE_ROOT,
        provenance_root=PROVENANCE_ROOT,
        evidence_refs=REFS,
        verifier_id="independent-verifier-1",
    )


def evaluate(**overrides):
    values = {
        "actor": "builder",
        "authority": "write",
        "capability": "code",
        "scope": "repo",
        "risk": "LOW",
        "baseline_sha": SHA,
        "policy_version": "p1",
        "policy_sha256": HASH,
        "evidence_root": EVIDENCE_ROOT,
        "provenance_root": PROVENANCE_ROOT,
        "evidence_refs": REFS,
        "human_approval": False,
        "verification_proof": verification_proof(),
    }
    values.update(overrides)
    return evaluate_authority_risk(**values)


class AEOSAssuranceFabricExpansionTests(unittest.TestCase):
    def test_open_ended_control_registration_is_deterministic(self):
        fabric = AssuranceFabric()
        fabric.register(compile_control_spec({
            "control_id": "C-001", "universe": "software", "plane": "change", "domain": "semantic_diff",
            "risk": "HIGH", "scope": "repo", "evidence_requirements": REFS,
            "verification_modes": ("DIRECT_OBSERVATION",), "failure_state": "UNKNOWN", "recovery_strategy": "REVIEW",
        }))
        self.assertEqual(fabric.coverage(), {"universes": 1, "planes": 1, "domains": 1, "controls": 1})

    def test_unknown_failure_cannot_assert_certification(self):
        with self.assertRaises(AssuranceFabricError):
            AssuranceControl("C-002", "u", "p", "d", "LOW", "repo", REFS, ("REPLAY",), "PASS", "REVIEW")

    def test_high_risk_requires_canonical_approval_proof(self):
        with self.assertRaises(AuthorityRiskError):
            evaluate(risk="HIGH", human_approval=True)

    def test_high_risk_accepts_approval_gate_proof(self):
        owner = OwnerIdentity(owner_id="aeos-approval-owner", display_name="Owner")
        request = FriendRequest(
            owner_id=owner.owner_id,
            profile_id="default",
            session_id="session-1",
            text="run command",
            requested_tools=("shell.run",),
        )
        gate = ApprovalGate()
        gate.approve(owner, request, "shell.run", reason="owner approved")
        approval_proof = gate.issue_proof(owner, request, "shell.run")
        result = evaluate(risk="HIGH", human_approval=False, approval_proof=approval_proof)
        self.assertTrue(result.allowed)
        self.assertTrue(result.human_approval)

    def test_high_risk_rejects_tampered_approval_proof(self):
        owner = OwnerIdentity(owner_id="aeos-approval-owner", display_name="Owner")
        request = FriendRequest(
            owner_id=owner.owner_id,
            profile_id="default",
            session_id="session-1",
            text="run command",
            requested_tools=("shell.run",),
        )
        gate = ApprovalGate()
        gate.approve(owner, request, "shell.run", reason="owner approved")
        proof = gate.issue_proof(owner, request, "shell.run")
        tampered = replace(proof, tool_name="shell")
        with self.assertRaises(AuthorityRiskError):
            evaluate(risk="HIGH", approval_proof=tampered)

    def test_approval_proof_rejects_non_approved_state(self):
        with self.assertRaises(ValueError):
            ApprovalProof(
                approval_id="a" * 64,
                owner_id="owner",
                profile_id="default",
                session_id="session",
                tool_name="shell.run",
                request_fingerprint="b" * 64,
                state=ApprovalState.PENDING,
                decided_at=None,
                evidence_digest="c" * 64,
            )

    def test_authority_risk_rejects_raw_verification_booleans(self):
        with self.assertRaises(TypeError):
            evaluate_authority_risk(actor="builder", authority="write", capability="code", scope="repo", risk="LOW", baseline_sha=SHA, policy_version="p1", policy_sha256=HASH, evidence_root=EVIDENCE_ROOT, provenance_root=PROVENANCE_ROOT, evidence_refs=REFS, human_approval=False, authority_verified=True, capability_verified=True, provenance_verified=True)  # type: ignore[call-arg]

    def test_authority_risk_accepts_verified_proof(self):
        proof = verification_proof()
        result = evaluate(verification_proof=proof)
        self.assertTrue(result.allowed)
        self.assertTrue(result.independently_verified)
        self.assertEqual(result.verification_digest, proof.evidence_digest)
        self.assertEqual(result.baseline_sha, SHA)
        self.assertEqual(result.evidence_root, EVIDENCE_ROOT)
        self.assertEqual(result.provenance_root, PROVENANCE_ROOT)

    def test_authority_risk_rejects_binding_mismatch(self):
        proof = verification_proof()
        for overrides in (
            {"baseline_sha": "e" * 40},
            {"policy_sha256": "f" * 64},
            {"evidence_root": "1" * 64},
            {"provenance_root": "2" * 64},
            {"evidence_refs": ("EV-001",)},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(AuthorityRiskError):
                    evaluate(verification_proof=proof, **overrides)

    def test_authority_risk_rejects_malformed_proof_roots(self):
        with self.assertRaises(AuthorityRiskError):
            build_authority_verification_proof(
                authority_verified=True, capability_verified=True, provenance_verified=True,
                baseline_sha=SHA, policy_version="p1", policy_sha256="not-a-sha",
                evidence_root=EVIDENCE_ROOT, provenance_root=PROVENANCE_ROOT,
                evidence_refs=REFS, verifier_id="independent-verifier-1",
            )

    def test_semantic_diff_marks_authority_change_critical(self):
        result = classify_semantic_diff(before={"authority": "read"}, after={"authority": "write"})
        self.assertTrue(result.breaking)
        self.assertEqual(result.risk, "CRITICAL")

    def test_semantic_diff_detects_nested_paths_and_input_fingerprints(self):
        result = classify_semantic_diff(
            before={"policy": {"permissions": {"write": False}}, "scope": ["repo"]},
            after={"policy": {"permissions": {"write": True}}, "scope": ["repo", "workspace"]},
        )
        self.assertEqual(result.changed, ("$.policy.permissions.write", "$.scope[1]"))
        self.assertTrue(result.breaking)
        self.assertEqual(len(result.before_digest), 64)
        self.assertEqual(len(result.after_digest), 64)
        self.assertEqual(len(result.change_proof), 2)

    def test_semantic_diff_is_deterministic(self):
        before = {"policy": {"z": 1, "a": 2}}
        after = {"policy": {"z": 3, "a": 2}}
        first = classify_semantic_diff(before=before, after=after)
        second = classify_semantic_diff(before=before, after=after)
        self.assertEqual(first, second)

    def test_semantic_diff_rejects_malformed_breaking_fields(self):
        with self.assertRaises(SemanticDiffError):
            classify_semantic_diff(before={}, after={"x": 1}, breaking_fields=("authority", ""))

    def test_blast_radius_is_transitive(self):
        result = calculate_blast_radius(root="a", dependencies={"b": ("a",), "c": ("b",), "d": ("c",)})
        self.assertEqual(result.affected, ("b", "c", "d"))

    def test_decision_replay_rejects_changed_output(self):
        record = record_decision(decision_id="D1", baseline_sha=SHA, contract_sha256=HASH, policy_sha256=HASH, inputs={"x": 1}, output={"ok": True}, evidence_refs=REFS)
        with self.assertRaises(DecisionReplayError):
            replay_decision(record=record, inputs={"x": 1}, output={"ok": False}, baseline_sha=SHA, contract_sha256=HASH, policy_sha256=HASH)

    def test_post_merge_rejects_unhealthy_runtime(self):
        with self.assertRaises(PostMergeVerificationError):
            verify_post_merge(expected_main_sha=SHA, observed_main_sha=SHA, ci_passed=True, runtime_healthy=False, evidence_refs=REFS)


if __name__ == "__main__":
    unittest.main()
