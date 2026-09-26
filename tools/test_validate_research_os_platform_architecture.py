import json
import unittest
from tools.validate_research_os_platform_architecture import main, INVENTORY, CONTRACT

class PlatformArchitectureAuditTests(unittest.TestCase):
    def test_platform_architecture_audit_passes(self):
        main()

    def test_registry_is_schema_driven_not_count_driven(self):
        inventory=json.loads(INVENTORY.read_text(encoding="utf-8"))
        components=inventory["components"]
        self.assertTrue(inventory["count_is_informational"])
        self.assertEqual(inventory["required_component_selection"], "component.required == true")
        self.assertEqual(len({item["id"] for item in components}), len(components))
        self.assertGreater(len(components), 0)

    def test_required_components_are_explicit(self):
        inventory=json.loads(INVENTORY.read_text(encoding="utf-8"))
        required=[item for item in inventory["components"] if item.get("required") is True]
        self.assertEqual(len(required), len(inventory["components"]))
        self.assertTrue(all(item["lifecycle"]=="ACTIVE" for item in required))

    def test_audit_contract_does_not_duplicate_component_set(self):
        contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertNotIn("required_component_ids", contract)
        self.assertEqual(contract["registry_validation"]["required_selector"], "component.required == true")

if __name__=="__main__":
    unittest.main()
