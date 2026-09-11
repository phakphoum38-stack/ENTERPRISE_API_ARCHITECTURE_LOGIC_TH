import unittest
from types import SimpleNamespace

from tools.aeos_master_composition import (
    MasterAssuranceSnapshot,
    compose_master_assurance,
    snapshot_from_results,
)


SHA = "a" * 40
EVIDENCE = "b" * 64


def result(set_id="SET-001", state="PASSED"):
    return SimpleNamespace(
        set_id=set_id,
        name=f"control-{set_id}",
        wave="IDENTITY",
        state=state,
        returncode=0 if state == "PASSED" else 1,
        command="true",
        cwd=".",
        duration_seconds=0.1,
        source_sha=SHA,
        iteration_id="iter-1",
        evidence_id=EVIDENCE,
        detail="ok",
    )


def snapshot():
    return MasterAssuranceSnapshot(
        iteration_id="iter-1",
        source_sha=SHA,
        result_digest="c" * 64,
        evidence_ids=(EVIDENCE,),
        wave_results=(("SET-001", "PASSED"),),
        execution_manifest_digest="d" * 64,
    )


def authority_packet(**overrides):
    data = {
        "original_change": "change",
        "original_failure": "failure",
        "root_cause": "RC-AEOS-ASSURANCE-COMPOSITION-BOUNDARY-001",
        "root_cause_proof": [EVIDENCE],
        "fix_attempts": ["attempt-1"],
        "final_fix": "composition boundary",
        "failed_controls_history": ["failure-1"],
        "resolved_failures": ["resolved-1"],
        "new_regressions": [],
        "exact_sha": SHA,
        "provenance": [EVIDENCE],
        "evidence_integrity": [EVIDENCE],
        "forensic_result": "PASS",
        "independent_review": "PASS",
        "remaining_risks": [],
        "remaining_assumptions": [],
        "assurance_debt": [],
        "recommended_decision": "APPROVE",
    }
    data.update(overrides)
    return data


def pre_authority_packet(**overrides):
    data = {
        "gate_id": "gate-1",
        "iteration_id": "iter-1",
        "source_sha": SHA,
        "required_waves": ["W0"],
        "wave_results": [["W0", "PASS"]],
        "holds": [],
        "evidence_ids": [EVIDENCE],
        "provenance_verified": True,
        "evidence_integrity_verified": True,
        "scope_verified": True,
        "root_cause_verified": True,
        "independent_review_verified": True,
        "assurance_self_check_verified": True,
        "remaining_risks": [],
        "remaining_assumptions": [],
        "assurance_debt": [],
    }
    data.update(overrides)
    return data


def proof(**overrides):
    data = {
        "authority_packet": authority_packet(),
        "pre_authority_packet": pre_authority_packet(),
    }
    data.update(overrides)
    return data


class MasterAssuranceCompositionTests(unittest.TestCase):
    def test_execution_pass_without_trust_proof_is_hold(self):
        composition = compose_master_assurance(snapshot=snapshot(), proof=None)
        self.assertEqual(composition.decision, "HOLD")
        self.assertEqual(composition.reason, "assurance_proof_missing")

    def test_complete_chain_is_ready_for_owner_authority(self):
        composition = compose_master_assurance(snapshot=snapshot(), proof=proof())
        self.assertEqual(composition.decision, "READY_FOR_OWNER_AUTHORITY")
        self.assertEqual(composition.reason, "assurance_composition_verified")

    def test_wrong_source_sha_is_hold(self):
        composition = compose_master_assurance(
            snapshot=snapshot(),
            proof=proof(authority_packet=authority_packet(exact_sha="e" * 40)),
        )
        self.assertEqual(composition.decision, "HOLD")
        self.assertEqual(composition.reason, "authority_packet_source_sha_mismatch")

    def test_wrong_iteration_is_hold(self):
        composition = compose_master_assurance(
            snapshot=snapshot(),
            proof=proof(pre_authority_packet=pre_authority_packet(iteration_id="iter-2")),
        )
        self.assertEqual(composition.decision, "HOLD")
        self.assertEqual(composition.reason, "pre_authority_iteration_mismatch")

    def test_unverified_review_is_not_ready(self):
        composition = compose_master_assurance(
            snapshot=snapshot(),
            proof=proof(pre_authority_packet=pre_authority_packet(independent_review_verified=False)),
        )
        self.assertEqual(composition.decision, "HOLD")
        self.assertTrue(composition.reason.startswith("pre_authority:"))

    def test_snapshot_binds_execution_identity(self):
        built = snapshot_from_results(
            iteration_id="iter-1",
            source_sha=SHA,
            results=[result()],
            execution_manifest_digest="d" * 64,
        )
        self.assertEqual(built.source_sha, SHA)
        self.assertEqual(built.iteration_id, "iter-1")
        self.assertEqual(built.evidence_ids, (EVIDENCE,))
        self.assertEqual(len(built.result_digest), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
