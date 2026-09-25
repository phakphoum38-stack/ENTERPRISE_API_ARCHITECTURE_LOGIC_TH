import unittest
from tools.validate_research_os_platform_architecture import main

class PlatformArchitectureAuditTests(unittest.TestCase):
    def test_platform_architecture_audit_passes(self):
        main()

    def test_required_component_set_is_complete(self):
        from tools.validate_research_os_platform_architecture import REQUIRED_IDS, CONTRACT, INVENTORY
        import json
        data=json.loads(CONTRACT.read_text(encoding="utf-8"))
        inventory=json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(set(REQUIRED_IDS), set(data["required_component_ids"]))
        self.assertEqual(len(REQUIRED_IDS), 18)
        components=inventory["components"]
        self.assertEqual(len(components), 18)
        self.assertEqual(len({item["id"] for item in components}), 18)
        self.assertEqual({item["id"] for item in components}, set(REQUIRED_IDS))
        for item in components:
            self.assertTrue((INVENTORY.parents[1] / item["canonical"]).exists())

if __name__=="__main__":
    unittest.main()
