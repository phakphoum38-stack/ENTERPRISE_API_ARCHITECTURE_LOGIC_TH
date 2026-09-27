import json
import unittest
from pathlib import Path

from platform_digital_twin import PlatformDigitalTwin

ROOT = Path(__file__).resolve().parents[1]

class PlatformDigitalTwinTests(unittest.TestCase):
    def test_snapshot_is_deterministic_and_read_only(self):
        twin = PlatformDigitalTwin(ROOT)
        first = twin.snapshot()
        second = twin.snapshot()
        self.assertEqual(first, second)
        self.assertGreater(first["node_count"], 0)
        self.assertGreaterEqual(first["edge_count"], 0)
        self.assertEqual(first["authority"], "READ_ONLY_PROJECTION")
        self.assertEqual(first["release_authority"], "FINAL_GATE")

    def test_unknown_impact_holds(self):
        result = PlatformDigitalTwin(ROOT).impact(["__unknown_component__"])
        self.assertEqual(result["result"]["status"], "HOLD")
        self.assertFalse(result["mutation"])
        self.assertFalse(result["authorization"])

    def test_simulation_does_not_acquire_authority(self):
        target = sorted(PlatformDigitalTwin(ROOT).spine.components)[0]
        result = PlatformDigitalTwin(ROOT).simulate([target])
        self.assertIn(result["status"], {"PASS", "FAIL", "HOLD"})
        self.assertFalse(result["mutation"])
        self.assertFalse(result["authorization"])

if __name__ == "__main__":
    unittest.main()
