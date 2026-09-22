import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_canonical_platform_contract.py"

spec = importlib.util.spec_from_file_location("validator", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CanonicalPlatformContractTests(unittest.TestCase):
    def setUp(self):
        self.data = module.load_contract(ROOT / "current" / "CANONICAL_PLATFORM_CONTRACT.yml")

    def test_contract_is_complete(self):
        self.assertEqual(module.validate(self.data), [])

    def test_resource_conflict_is_fail_closed(self):
        self.data["resource_conflict"]["same_version_overwrite"] = True
        self.assertTrue(module.validate(self.data))

    def test_sha_and_provenance_are_bound(self):
        self.data["identity"]["source_sha"]["head_must_match"] = False
        self.assertTrue(module.validate(self.data))

    def test_final_gate_remains_authority(self):
        self.data["authority"]["final_gate_is_release_authority"] = False
        self.assertTrue(module.validate(self.data))


if __name__ == "__main__":
    unittest.main()
