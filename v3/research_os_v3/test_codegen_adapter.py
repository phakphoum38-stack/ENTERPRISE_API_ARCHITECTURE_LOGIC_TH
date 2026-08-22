import unittest

from .codegen_adapter import CodeGenerationRequest, ExistingCodeGeneratorAdapter
from .models import OrchestrationDecision, SCALE_PROFILES
from .providers import MockProvider, ProviderRegistry


class CodeGeneratorAdapterTests(unittest.TestCase):
    def test_existing_provider_generates_auditable_output(self) -> None:
        adapter = ExistingCodeGeneratorAdapter(ProviderRegistry([MockProvider()]))
        request = CodeGenerationRequest(
            task="add a safe adapter",
            repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            base_sha="5f84d78c624fadf027acff0527f60b743744f0e5",
            constraints={"no_direct_main_write": True},
        )
        decision = OrchestrationDecision(
            profile=SCALE_PROFILES[0],
            provider="mock",
            demand=1,
            reason="integration test",
        )

        result = adapter.generate(request, decision=decision)

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.provider, "mock")
        self.assertEqual(result.model, "mock")
        self.assertEqual(result.base_sha, request.base_sha)
        self.assertTrue(result.output)
        self.assertEqual(len(result.output_sha256), 64)
        self.assertEqual(result.evidence.name, "codegen")
        self.assertEqual(result.evidence.status, "passed")

    def test_adapter_does_not_mutate_repository(self) -> None:
        adapter = ExistingCodeGeneratorAdapter(ProviderRegistry([MockProvider()]))
        request = CodeGenerationRequest(
            task="produce a proposed change",
            repository="repo",
            base_sha="abc123",
            constraints={},
        )

        result = adapter.generate(request)

        self.assertEqual(result.base_sha, "abc123")
        self.assertNotIn("git commit", result.output.lower())


if __name__ == "__main__":
    unittest.main()
