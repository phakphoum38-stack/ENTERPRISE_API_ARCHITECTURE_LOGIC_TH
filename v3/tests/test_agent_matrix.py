from __future__ import annotations

import unittest

from research_os_v3.agent_matrix import (
    AGENT_MATRIX,
    GUARDIANS,
    LOGICAL_AGENT_MATRIX,
    validate_agent_matrix,
    validate_logical_agent_matrix,
    select_logical_agents,
)


class AgentMatrixTests(unittest.TestCase):
    def test_matrix_has_six_domains_and_six_agents_each(self) -> None:
        self.assertEqual(len(AGENT_MATRIX), 6)
        self.assertTrue(all(len(agents) == 6 for agents in AGENT_MATRIX.values()))
        self.assertEqual(len(GUARDIANS), 3)

    def test_matrix_is_unique_and_valid(self) -> None:
        self.assertEqual(validate_agent_matrix(AGENT_MATRIX), [])

    def test_runtime_profile_has_six_sets_and_eleven_agents(self) -> None:
        self.assertEqual(len(LOGICAL_AGENT_MATRIX), 11)
        self.assertEqual(len({agent.agent_set for agent in LOGICAL_AGENT_MATRIX}), 6)
        self.assertEqual(validate_logical_agent_matrix(), [])

    def test_dynamic_selection_is_bounded_and_deterministic(self) -> None:
        selected = select_logical_agents(("research", "evidence_qa"), concurrency=3)
        self.assertEqual([agent.agent_id for agent in selected], ["A2", "A3", "A8"])


if __name__ == "__main__":
    unittest.main()
