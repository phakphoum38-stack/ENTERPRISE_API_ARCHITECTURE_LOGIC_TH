from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVARIANTS = REPO_ROOT / "current" / "ARCHITECTURE_INVARIANTS.md"


class ArchitectureInvariantContractTests(unittest.TestCase):
    def test_canonical_invariants_document_exists(self) -> None:
        self.assertTrue(INVARIANTS.is_file())

    def test_required_invariant_ids_are_present(self) -> None:
        text = INVARIANTS.read_text(encoding="utf-8")
        for invariant in range(1, 21):
            self.assertIn(f"INV-{invariant:03d}", text)

    def test_enforcement_rule_rejects_document_only_evidence(self) -> None:
        text = INVARIANTS.read_text(encoding="utf-8")
        self.assertIn("A document alone is not considered proof that an invariant is enforced.", text)
        self.assertIn("Contract / schema", text)
        self.assertIn("Unit or integration test", text)
        self.assertIn("Validator / audit", text)
        self.assertIn("CI gate", text)


if __name__ == "__main__":
    unittest.main()
