from __future__ import annotations
import json
import unittest
from pathlib import Path
from tools.validate_owner_experience_platform import main
class OwnerExperiencePlatformTests(unittest.TestCase):
    def test_platform_contract_is_valid(self): main()
    def test_owner_authority_boundary(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/"current/RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertTrue(data["owner"]["highest_privilege"]); self.assertFalse(data["owner"]["resource_or_scope_bound"])
        self.assertFalse(data["owner"]["ui_may_authorize"]); self.assertFalse(data["owner"]["ui_may_execute"])
        self.assertFalse(data["owner_special"]["canonical_product_ui"])
    def test_shared_surface(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/"current/RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertTrue(data["cross_platform"]["windows"]); self.assertTrue(data["cross_platform"]["web"]); self.assertTrue(data["cross_platform"]["ios"])
        self.assertTrue(data["cross_platform"]["same_product_surface_contract"])
if __name__ == "__main__": unittest.main()
