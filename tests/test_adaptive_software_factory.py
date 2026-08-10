import tempfile
import unittest
from pathlib import Path

from software_factory import AdaptiveControlPlane, AdaptiveHierarchyPlanner


class AdaptiveHierarchyPlannerTests(unittest.TestCase):
    def test_profile_selection(self) -> None:
        planner = AdaptiveHierarchyPlanner()
        self.assertEqual(planner.choose_profile(1).label, "1^3")
        self.assertEqual(planner.choose_profile(10).label, "3^3")
        self.assertEqual(planner.choose_profile(100).label, "6^3")
        self.assertEqual(planner.choose_profile(1000).label, "6^6")

    def test_only_requested_factories_are_activated(self) -> None:
        planner = AdaptiveHierarchyPlanner()
        plan = planner.plan(f"v{index}" for index in range(1, 11))
        self.assertEqual(plan.profile.label, "3^3")
        self.assertEqual(plan.active_factories, 10)
        assigned = [
            version
            for node in plan.root.walk()
            for version in node.assigned_versions
        ]
        self.assertEqual(len(assigned), 10)
        self.assertEqual(len(set(assigned)), 10)

    def test_duplicate_versions_do_not_create_duplicate_factories(self) -> None:
        plan = AdaptiveHierarchyPlanner().plan(["v1", "v1", "v2"])
        self.assertEqual(plan.active_factories, 2)


class AdaptiveControlPlaneTests(unittest.TestCase):
    def test_version_factory_has_full_specialist_team(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plane = AdaptiveControlPlane(Path(directory))
            plane.configure_versions(["v1"])
            factory = plane.factory_for("v1")
            self.assertEqual(len(factory.agent_ids()), 9)

    def test_factory_write_boundary_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plane = AdaptiveControlPlane(root)
            plane.configure_versions(["v1"])
            factory = plane.factory_for("v1")
            allowed = factory.worktree_root / "src" / "feature.py"
            plane.begin_write("v1", allowed)
            plane.end_write("v1", allowed)

            with self.assertRaises(PermissionError):
                plane.begin_write("v1", root / "outside.py")

    def test_summary_reports_logical_capacity_not_eager_allocation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plane = AdaptiveControlPlane(Path(directory))
            plane.configure_versions(f"v{index}" for index in range(1, 101))
            summary = plane.summary()
            self.assertEqual(summary["profile"], "6^3")
            self.assertEqual(summary["logical_capacity"], 216)
            self.assertEqual(summary["active_factories"], 100)


if __name__ == "__main__":
    unittest.main()
