import unittest

from tools.native_control_plane import (
    AssuranceEngine,
    AssuranceState,
    Command,
    CommandPhase,
    ControlEngine,
    Evidence,
    ExperienceEngine,
    KnowledgeEngine,
    KnowledgeObject,
    KnowledgeState,
    ResearchOSControlPlane,
    View,
    ViewState,
)


class NativeControlPlaneTests(unittest.TestCase):
    def test_control_dispatch_is_bounded_and_lineaged(self):
        engine = ControlEngine(max_commands=1)
        record = engine.dispatch(
            Command("cmd-1", "inspect", "open", risk="LOW"),
            observed=True,
            evidence_refs=("EV-1",),
        )
        self.assertEqual(record.phases[0], CommandPhase.INTENT)
        self.assertEqual(record.phases[-1], CommandPhase.COMPLETE)
        self.assertEqual(record.outcome, "COMPLETED")
        with self.assertRaises(RuntimeError):
            engine.dispatch(Command("cmd-2", "inspect", "open"))

    def test_high_risk_requires_human_authorization(self):
        engine = ControlEngine()
        with self.assertRaises(PermissionError):
            engine.dispatch(Command("cmd-1", "release", "merge", risk="HIGH"))
        record = engine.dispatch(
            Command("cmd-2", "release", "merge", risk="HIGH", requires_human=True),
            authorized=True,
        )
        self.assertIn(CommandPhase.AUTHORIZE, record.phases)

    def test_experience_state_transition(self):
        engine = ExperienceEngine()
        engine.register(View("home", "Home", "/"))
        self.assertEqual(engine.transition("home", ViewState.ACTIVE).state, ViewState.ACTIVE)

    def test_knowledge_confidence_requires_evidence(self):
        engine = KnowledgeEngine()
        engine.register(KnowledgeObject("k1", "OBSERVATION"))
        with self.assertRaises(ValueError):
            engine.transition("k1", KnowledgeState.CONFIDENT)
        obj = engine.transition("k1", KnowledgeState.EVIDENCED, evidence_refs=("EV-1",))
        self.assertEqual(obj.evidence_refs, ("EV-1",))

    def test_assurance_fingerprint_and_verification(self):
        engine = AssuranceEngine()
        with self.assertRaises(ValueError):
            engine.record(Evidence("EV-1", "k1", "source:1", "bad"))
        engine.record(Evidence("EV-1", "k1", "source:1", "a" * 64))
        self.assertEqual(engine.verify("EV-1").state, AssuranceState.VERIFIED)

    def test_universal_inspector_composes_knowledge_and_evidence(self):
        plane = ResearchOSControlPlane()
        plane.knowledge.register(KnowledgeObject("k1", "OBSERVATION", KnowledgeState.EVIDENCED, evidence_refs=("EV-1",)))
        plane.assurance.record(Evidence("EV-1", "k1", "source:1", "b" * 64))
        inspected = plane.inspect("k1")
        self.assertEqual(inspected["knowledge"]["state"], "EVIDENCED")
        self.assertEqual(inspected["evidence"][0]["id"], "EV-1")
        self.assertEqual(plane.summary()["knowledge_objects"], 1)


if __name__ == "__main__":
    unittest.main()
