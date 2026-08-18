from __future__ import annotations

import unittest

from research_os_v3.agent_matrix import AGENT_MATRIX, GUARDIANS, validate_agent_matrix


class AgentMatrixTests(unittest.TestCase):
    def test_matrix_has_six_domains_and_six_agents_each(self) -> None:
        self.assertEqual(len(AGENT_MATRIX), 6)
        self.assertTrue(all(len(agents) == 6 for agents in AGENT_MATRIX.values()))
        self.assertEqual(len(GUARDIANS), 3)

    def test_matrix_is_unique_and_valid(self) -> None:
        errors = validate_agent_matrix(AGENT_MATRIX)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
