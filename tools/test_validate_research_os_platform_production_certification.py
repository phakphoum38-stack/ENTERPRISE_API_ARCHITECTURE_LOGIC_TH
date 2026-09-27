import json
import unittest

from tools.validate_research_os_platform_production_certification import (
    CONTRACT,
    main,
    validate_contract_semantics,
)


class ProductionCertificationTest(unittest.TestCase):
    def test_certification(self):
        self.assertEqual(main(), 0)

    def test_contract_semantics_are_complete(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(validate_contract_semantics(contract), [])

    def test_required_surface_count(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(len(contract["required_surfaces"]), 11)

    def test_continuity_workflow_is_certified(self):
        from tools.validate_research_os_platform_production_certification import REQUIRED
        self.assertIn("current/RESEARCH_OS_PLATFORM_CONTINUITY_WORKFLOW_CONTRACT.json", REQUIRED)
        self.assertIn("tools/platform_continuity_workflow.py", REQUIRED)
        self.assertIn("tools/test_platform_continuity_workflow.py", REQUIRED)

    def test_required_evidence_count(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(len(contract["evidence"]), 6)


if __name__ == "__main__":
    unittest.main()
