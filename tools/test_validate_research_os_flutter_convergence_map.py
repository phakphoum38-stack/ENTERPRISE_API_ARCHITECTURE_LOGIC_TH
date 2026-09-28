import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_research_os_flutter_convergence_map.py"
spec = importlib.util.spec_from_file_location("convergence_validator", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ConvergenceMapTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(
            (ROOT / "current" / "RESEARCH_OS_FLUTTER_CONVERGENCE_MAP.json").read_text(
                encoding="utf-8"
            )
        )

    def test_contract_is_valid(self):
        self.assertEqual(module.validate(self.data), [])

    def test_all_three_roots_are_present(self):
        roots = {entry["root"] for entry in self.data["roots"]}
        self.assertEqual(
            roots,
            {"owner_special/flutter_app", "apps/research_os_flutter", "v3/flutter_app"},
        )

    def test_retirement_is_not_authorized(self):
        self.assertEqual(
            self.data["retirement_policy"],
            "NO_DELETE_UNTIL_PARITY_AND_ALL_APPLICABLE_GATES_PASS",
        )
        self.assertTrue(all(not entry["retire"] for entry in self.data["roots"]))

    def test_no_unknown_classification(self):
        allowed = set(self.data["classifications"])
        for root in self.data["roots"]:
            for feature in root["features"]:
                self.assertIn(feature["classification"], allowed)


if __name__ == "__main__":
    unittest.main()
