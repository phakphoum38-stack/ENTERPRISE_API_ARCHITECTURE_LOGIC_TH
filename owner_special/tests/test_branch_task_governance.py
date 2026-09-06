from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "current" / "BRANCH_TASK_GOVERNANCE.yml"
DOCUMENT = ROOT / "current" / "BRANCH_TASK_GOVERNANCE.md"
VALIDATOR = ROOT / "tools" / "validate_branch_task_governance.py"


class BranchTaskGovernanceContractTests(unittest.TestCase):
    def test_canonical_governance_assets_exist(self) -> None:
        self.assertTrue(CONTRACT.is_file())
        self.assertTrue(DOCUMENT.is_file())
        self.assertTrue(VALIDATOR.is_file())

    def test_contract_is_fail_closed(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        for phrase in (
            "one_task_one_branch: true",
            "exact_base_sha_required: true",
            "exact_head_sha_required: true",
            "failed_branch_becomes_quarantined: true",
            "unknown_state_cannot_be_base: true",
            "unknown_base_sha_cannot_be_base: true",
            "merge_requires_explicit_authorization: true",
        ):
            self.assertIn(phrase, text)

    def test_document_forbids_implicit_base_selection(self) -> None:
        text = DOCUMENT.read_text(encoding="utf-8")
        self.assertIn("UNKNOWN branch state or UNKNOWN base SHA must never be used", text)
        self.assertIn("One logical task has one working branch.", text)
        self.assertIn("A mutable branch under verification is LOCKED", text)


if __name__ == "__main__":
    unittest.main()
