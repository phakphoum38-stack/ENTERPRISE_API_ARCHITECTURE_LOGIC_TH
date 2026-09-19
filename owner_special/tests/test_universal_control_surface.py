import unittest

from tools.universal_control_surface import CommandSpec, SurfaceObject, UniversalControlSurface


class UniversalControlSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.surface = UniversalControlSurface()
        self.surface.register_object(SurfaceObject(
            object_id="TASK-001", object_type="TASK", title="Research control center",
            state="OBSERVED", relations=("EV-001", "SERVICE-001"), dependencies=("SERVICE-001",)))
        self.surface.register_object(SurfaceObject(
            object_id="EV-001", object_type="EVIDENCE", title="Control Center runtime evidence",
            state="VERIFIED", provenance="sha256:test"))
        self.surface.register_object(SurfaceObject(
            object_id="SERVICE-001", object_type="SERVICE", title="Owner Friend runtime", state="RUNNING"))

    def test_search_is_bounded_and_deterministic(self) -> None:
        hits = self.surface.search("control center")
        self.assertEqual([hit.object_id for hit in hits], ["TASK-001", "EV-001"])
        self.assertEqual(self.surface.search("runtime", domain="SERVICE")[0].object_id, "SERVICE-001")

    def test_unknown_object_fails_closed(self) -> None:
        with self.assertRaises(KeyError):
            self.surface.inspect("MISSING")

    def test_trace_preserves_lineage_without_authority(self) -> None:
        trace = self.surface.trace("TASK-001", depth=2)
        self.assertEqual(trace[0].object_id, "TASK-001")
        self.assertIn("EV-001", {step.object_id for step in trace})
        self.assertIn("SERVICE-001", {step.object_id for step in trace})

    def test_command_preparation_is_not_execution(self) -> None:
        self.surface.register_command(CommandSpec(
            command_id="CMD-001", label="Inspect runtime", intent="Observe runtime state",
            target="SERVICE-001", mode="SIMULATION"))
        fingerprint = self.surface.prepare_command("CMD-001")
        self.assertEqual(len(fingerprint), 64)
        self.assertFalse(self.surface.human_required("OBSERVE"))
        self.assertTrue(self.surface.human_required("AUTHORIZE"))

    def test_system_map_uses_existing_planes(self) -> None:
        system_map = self.surface.system_map()
        self.assertIn("TASK-001", system_map["CORE"])
        self.assertIn("EV-001", system_map["ASSURANCE"])
        self.assertIn("SERVICE-001", system_map["PLATFORM"])
        self.assertEqual(system_map["EXPERIENCE"], ())

    def test_fingerprint_is_stable(self) -> None:
        self.assertEqual(self.surface.fingerprint(), self.surface.fingerprint())


if __name__ == "__main__":
    unittest.main()
