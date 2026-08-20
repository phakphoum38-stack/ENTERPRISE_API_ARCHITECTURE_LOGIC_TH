from __future__ import annotations

from .factory import CodeFactory
from .memory import MemoryStore
from .models import ConversationTurn, Evidence, PluginManifest, VerificationResult
from .plugins import PluginRegistry
from .research import ResearchIndex
from .verification import VerificationEngine


class AssistantOrchestrator:
    """Small deterministic coordinator; model/provider execution stays behind plugins."""

    def __init__(self) -> None:
        self.memory = MemoryStore()
        self.plugins = PluginRegistry()
        self.research = ResearchIndex()
        self.factory = CodeFactory()
        self.verifier = VerificationEngine()

    def remember(self, role: str, content: str, **metadata: object) -> None:
        self.memory.append(ConversationTurn(role=role, content=content, metadata=metadata))

    def register_plugin(self, manifest: PluginManifest, handler) -> None:
        self.plugins.register(manifest, handler)

    def add_evidence(self, evidence: Evidence) -> None:
        self.research.add(evidence)

    def generate_python(self, path: str, source: str, purpose: str) -> VerificationResult:
        artifact = self.factory.build_python(path, source, purpose)
        evidence = self.research.trusted()
        return self.verifier.verify_artifact(artifact, evidence=evidence)

    def capabilities(self) -> dict[str, object]:
        return {
            "memory": True,
            "research_evidence": True,
            "code_factory": True,
            "verification": True,
            "plugins": [m.name for m in self.plugins.list_enabled()],
        }
