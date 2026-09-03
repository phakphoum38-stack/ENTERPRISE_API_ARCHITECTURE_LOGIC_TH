from __future__ import annotations

import json
import unittest

from research_os_friend.launch_desk import (
    READINESS_AREAS,
    build_deterministic_plan,
    check_launch_readiness,
    extract_tasks,
    generate_owner_checklist,
)


class LaunchDeskTests(unittest.TestCase):
    def test_extract_tasks_is_deterministic(self) -> None:
        tasks = extract_tasks("QA blocker: run release tests\nDocs: publish operator guide")
        self.assertEqual([task["priority"] for task in tasks], ["P0", "P1"])
        self.assertEqual(tasks[0]["area"], "QA")
        self.assertEqual(tasks[1]["area"], "docs")

    def test_readiness_uses_all_nine_areas(self) -> None:
        result = check_launch_readiness("product and QA are confirmed", extract_tasks("product and QA are confirmed"))
        self.assertEqual([item["area"] for item in result["items"]], list(READINESS_AREAS))
        self.assertEqual(result["score"], 49)

    def test_owner_checklist_flags_missing_evidence(self) -> None:
        result = check_launch_readiness("security", extract_tasks("security"))
        checklist = generate_owner_checklist(result)
        self.assertTrue(checklist)
        self.assertTrue(any("engineering" in item for item in checklist))

    def test_plan_contains_required_surfaces(self) -> None:
        from research_os_friend.launch_desk import build_deterministic_plan
        plan = build_deterministic_plan("Ship Research OS after QA validation")
        payload = plan.to_dict()
        for key in ("tasks", "readiness", "readiness_score", "risks", "owner_checklist", "launch_copy", "follow_up_questions", "assumptions"):
            self.assertIn(key, payload)
        self.assertEqual(len(payload["readiness"]), 9)
        self.assertIn("Readiness is currently", payload["launch_copy"])

    def test_tool_outputs_are_json(self) -> None:
        from research_os_friend.launch_desk import LaunchDeskTools
        self.assertIsInstance(json.loads(LaunchDeskTools.extract_tasks("QA")), list)
        self.assertIsInstance(json.loads(LaunchDeskTools.check_launch_readiness("QA")), dict)
        self.assertIsInstance(json.loads(LaunchDeskTools.generate_owner_checklist("QA")), list)
        self.assertIsInstance(LaunchDeskTools.draft_launch_copy("QA"), str)


if __name__ == "__main__":
    unittest.main()
