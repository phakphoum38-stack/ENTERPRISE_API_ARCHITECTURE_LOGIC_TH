import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_research_os_unified_ux",
    ROOT / "tools/validate_research_os_unified_ux.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UnifiedUXContractTest(unittest.TestCase):
    def test_contract_passes(self):
        self.assertEqual(MODULE.validate(), [])

    def test_platform_owns_contract(self):
        data = MODULE.json.loads(MODULE.CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(data["authority"], "PLATFORM")

    def test_beam_is_not_persistent_background(self):
        data = MODULE.json.loads(MODULE.CONTRACT.read_text(encoding="utf-8"))
        self.assertFalse(data["light_beam"]["persistent_background_beam"])

    def test_all_target_surfaces_are_bound(self):
        data = MODULE.json.loads(MODULE.CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(set(data["surfaces"]), {"WINDOWS", "WEB", "IOS"})


if __name__ == "__main__":
    unittest.main()
