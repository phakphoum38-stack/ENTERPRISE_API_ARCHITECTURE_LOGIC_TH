import unittest

from assistant_core import (
    AssistantOrchestrator,
    ConversationTurn,
    Evidence,
    MemoryStore,
    NaturalConversationPolicy,
    PluginManifest,
)


class AssistantCoreTests(unittest.TestCase):
    def test_memory_is_bounded_and_searchable(self):
        memory = MemoryStore(max_turns=2)
        memory.append(ConversationTurn("user", "first"))
        memory.append(ConversationTurn("assistant", "second"))
        memory.append(ConversationTurn("user", "third"))
        self.assertEqual([t.content for t in memory.recent()], ["second", "third"])
        self.assertEqual(memory.search("SECOND")[0].role, "assistant")

    def test_plugin_registry_is_detachable(self):
        orchestrator = AssistantOrchestrator()
        manifest = PluginManifest("demo", "1.0.0", ("echo",), "tests.demo")
        orchestrator.register_plugin(manifest, lambda value: value.upper())
        self.assertEqual(orchestrator.plugins.invoke("demo", "ok"), "OK")
        orchestrator.plugins.unregister("demo")
        self.assertEqual(orchestrator.plugins.list_enabled(), ())

    def test_research_requires_valid_evidence(self):
        orchestrator = AssistantOrchestrator()
        orchestrator.add_evidence(Evidence("official", "API", "https://example.com/api", 0.95))
        result = orchestrator.generate_python("generated.py", "x = 1\n", "smoke")
        self.assertTrue(result.passed)
        self.assertIn("trusted-evidence", result.checks)

    def test_invalid_python_is_rejected(self):
        orchestrator = AssistantOrchestrator()
        with self.assertRaises(SyntaxError):
            orchestrator.factory.build_python("generated.py", "def broken(:\n", "negative")

    def test_no_evidence_blocks_release_verification(self):
        orchestrator = AssistantOrchestrator()
        result = orchestrator.generate_python("generated.py", "x = 1\n", "no evidence")
        self.assertFalse(result.passed)
        self.assertIn("no trusted evidence", result.failures)

    def test_natural_conversation_policy_removes_ai_boilerplate(self):
        policy = NaturalConversationPolicy(max_context_turns=2)
        self.assertEqual(policy.normalize("  As an AI,  hello   there. "), "hello there.")
        self.assertEqual(len(policy.context((ConversationTurn("user", "1"), ConversationTurn("user", "2")))), 2)


if __name__ == "__main__":
    unittest.main()
