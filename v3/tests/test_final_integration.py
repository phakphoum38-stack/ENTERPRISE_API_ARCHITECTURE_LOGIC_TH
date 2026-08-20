from __future__ import annotations

import unittest

from research_os_v3.final_integration import FinalIntegrationGate


class FinalIntegrationGateTests(unittest.TestCase):
    def test_all_gates_must_pass(self) -> None:
        gate = FinalIntegrationGate((("build", lambda: True), ("e2e", lambda: True)))
        results = gate.run()
        self.assertTrue(FinalIntegrationGate.passed(results))

    def test_failure_is_reported_and_blocks_release(self) -> None:
        gate = FinalIntegrationGate((("build", lambda: True), ("security", lambda: False)))
        results = gate.run()
        self.assertFalse(FinalIntegrationGate.passed(results))
        self.assertFalse(results[1].success)

    def test_exception_fails_closed(self) -> None:
        def broken() -> bool:
            raise RuntimeError("boom")

        results = FinalIntegrationGate((("broken", broken),)).run()
        self.assertFalse(results[0].success)
        self.assertIn("RuntimeError", results[0].detail)


if __name__ == "__main__":
    unittest.main()
