from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.validate_universal_learning import validate


class UniversalLearningContractTests(unittest.TestCase):
    def load(self) -> dict:
        return json.loads(
            Path("current/UNIVERSAL_LEARNING_CONTRACT.json").read_text(encoding="utf-8")
        )

    def test_contract_validates(self) -> None:
        fingerprint = validate(self.load())
        self.assertEqual(len(fingerprint), 64)

    def test_contract_uses_mathematical_root(self) -> None:
        contract = self.load()
        self.assertEqual(contract["mathematical_root"]["symbol"], "10^1000")
        self.assertEqual(
            contract["mathematical_root"]["materialization"],
            "forbidden",
        )

    def test_unknown_is_contractual(self) -> None:
        self.assertIn("UNKNOWN", self.load()["knowledge_kinds"])

    def test_merge_authority_remains_separate(self) -> None:
        self.assertEqual(
            self.load()["authority"]["merge_authority"],
            "unchanged",
        )

    def test_contract_is_deterministic(self) -> None:
        contract = self.load()
        self.assertEqual(validate(contract), validate(contract))


if __name__ == "__main__":
    unittest.main()
