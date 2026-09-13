import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_engineering_world_model import validate

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "current" / "ENGINEERING_WORLD_MODEL_SCHEMA.json"
FIXTURE = ROOT / "current" / "ENGINEERING_WORLD_MODEL_FIXTURE.json"


class EngineeringWorldModelTests(unittest.TestCase):
    def test_fixture_validates(self):
        self.assertEqual(validate(SCHEMA, FIXTURE), [])

    def test_duplicate_entity_fails(self):
        graph = json.loads(FIXTURE.read_text(encoding="utf-8"))
        graph["entities"].append(copy.deepcopy(graph["entities"][0]))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "graph.json"
            p.write_text(json.dumps(graph), encoding="utf-8")
            self.assertIn("duplicate entity id", validate(SCHEMA, p))

    def test_missing_endpoint_fails(self):
        graph = json.loads(FIXTURE.read_text(encoding="utf-8"))
        graph["relationships"][0]["to"] = "MISSING"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "graph.json"
            p.write_text(json.dumps(graph), encoding="utf-8")
            self.assertIn("relationship R1: endpoint missing", validate(SCHEMA, p))


if __name__ == "__main__":
    unittest.main()
