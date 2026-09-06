from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .brain import FriendBrain
from .capabilities import CapabilityRegistry, install_friend_complete_capabilities
from .catalog import install_builtin_skills, install_builtin_tools
from .evidence import EvidenceRecorder
from .helpers import HelperScheduler
from .identity import OwnerIdentity
from .memory import ScopedMemory
from .models import FriendRequest, FriendResponse
from .orchestrator import FriendOrchestrator
from .persistent_memory import PersistentScopedMemory
from .policy import OwnerPolicy
from .providers import MockProvider, ProviderRouter
from .provider_settings import OpenAICompatibleProvider, UrllibJsonTransport
from .schedule_generation.preview import SchedulePreviewStore
from .reasoning import DecisionPlanner
from .self_learning import SelfLearningEngine
from .skills import SkillRegistry
from .tools import ToolRegistry
from .tool_health import ToolHealthMatrix
from .tool_health_gate import ToolHealthGate
from .unified_tool_catalog import UnifiedToolCatalog
from .v3_bridge import V3Bridge
from .v3_execution_adapter import V3ExecutionAdapter


@dataclass
class FriendRuntime:
    owner: OwnerIdentity
    orchestrator: FriendOrchestrator
    capabilities: CapabilityRegistry
    bridge: V3Bridge
    helpers: HelperScheduler
    v3: V3ExecutionAdapter
    data_root: Path | None = None
    previews: SchedulePreviewStore | None = None
    self_learning: SelfLearningEngine | None = None

    @classmethod
    def create_owner_special(cls, owner_id: str, *, display_name: str = "Owner", evidence_path: Path | None = None, data_root: Path | None = None, repository_root: Path | None = None) -> "FriendRuntime":
        repo_root = (
            Path(repository_root).resolve()
            if repository_root is not None
            else Path(__file__).resolve().parents[2]
        )
        owner = OwnerIdentity(owner_id=owner_id, display_name=display_name)
        skills = install_builtin_skills(SkillRegistry())
        tools = install_builtin_tools(ToolRegistry())
        providers = ProviderRouter()

        # Keep the deterministic mock as the safe offline fallback, but use a
        # real OpenAI-compatible provider automatically when the host supplies
        # OPENAI_API_KEY. The credential is never persisted by this path.
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if api_key:
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
            model = os.environ.get("OPENAI_MODEL", "gpt-5-mini").strip()
            providers.register(
                OpenAICompatibleProvider(
                    base_url=base_url,
                    model=model,
                    api_key=api_key,
                    transport=UrllibJsonTransport(),
                )
            )
        providers.register(MockProvider())

        capabilities = install_friend_complete_capabilities()
        bridge = V3Bridge(repo_root)
        v3 = V3ExecutionAdapter()
        normalized_root = Path(data_root).resolve() if data_root is not None else None
        if normalized_root is None:
            memory: ScopedMemory = ScopedMemory()
            previews = SchedulePreviewStore(Path.cwd() / ".research_os_previews")
        else:
            owner_root = normalized_root / "owners" / owner.owner_id
            memory = PersistentScopedMemory(owner_root / "memory" / "memory.json")
            previews = SchedulePreviewStore(normalized_root)
            if evidence_path is None:
                evidence_path = owner_root / "evidence" / "events.jsonl"
        orchestrator = FriendOrchestrator(owner=owner, brain=FriendBrain(bridge), planner=DecisionPlanner(), skills=skills, tools=tools, providers=providers, memory=memory, policy=OwnerPolicy(), evidence=EvidenceRecorder(evidence_path))
        return cls(owner=owner, orchestrator=orchestrator, capabilities=capabilities, bridge=bridge, helpers=HelperScheduler(), v3=v3, data_root=normalized_root, previews=previews, self_learning=SelfLearningEngine())

    def ask(self, request: FriendRequest) -> FriendResponse:
        return self.orchestrator.handle(request)

    def tool_catalog(self) -> tuple[dict[str, object], ...]:
        """Expose read-only tool discovery and health without changing execution ownership."""
        return UnifiedToolCatalog().health_matrix(
            friend_tools=self.orchestrator.tools.names(),
            v3_tools=self.v3.names(),
        )

    def tool_health(self) -> dict[str, object]:
        """Return aggregate catalog health plus the execution readiness gate."""
        catalog_snapshot = ToolHealthMatrix().snapshot(
            friend_tools=self.orchestrator.tools.names(),
            v3_tools=self.v3.names(),
        )
        gate_snapshot = ToolHealthGate().snapshot(
            friend_tools=self.orchestrator.tools.names(),
            v3_tools=self.v3.names(),
        )
        return {
            **catalog_snapshot,
            "gate": gate_snapshot,
        }

    def tool_health_gate(self) -> dict[str, object]:
        """Return the deterministic readiness gate used by the Friend runtime."""
        return ToolHealthGate().snapshot(
            friend_tools=self.orchestrator.tools.names(),
            v3_tools=self.v3.names(),
        )

    def learn_skill(self, *, name: str, goal: str, procedure: tuple[str, ...], evidence: tuple[str, ...] = (), confidence: float = 0.0):
        """Propose and promote a learned skill through the bounded approval gate."""
        if self.self_learning is None:
            self.self_learning = SelfLearningEngine()
        candidate = self.self_learning.propose(
            name=name,
            goal=goal,
            procedure=procedure,
            evidence=evidence,
            confidence=confidence,
        )
        return self.self_learning.learn(candidate)

    def self_learning_snapshot(self) -> dict[str, object]:
        """Expose learning state without exposing or mutating the core skill registry."""
        if self.self_learning is None:
            self.self_learning = SelfLearningEngine()
        return self.self_learning.snapshot()

    def execute_v3(
        self,
        request: FriendRequest,
        *,
        capability: str,
        input: dict[str, object],
        task_id: str | None = None,
    ):
        """Execute an explicitly requested V3 capability behind the owner boundary."""
        self.orchestrator.policy.authorize_request(self.owner, request)
        return self.v3.execute(
            owner_id=self.owner.owner_id,
            request_owner_id=request.owner_id,
            requested_tools=request.requested_tools,
            capability=capability,
            input=input,
            task_id=task_id,
        )

    def architecture(self) -> dict[str, object]:
        persistence = "disk" if isinstance(self.orchestrator.memory, PersistentScopedMemory) else "memory"
        return {
            "edition": self.owner.edition,
            "owner_id": self.owner.owner_id,
            "brain_profiles": self.bridge.scale_profiles(),
            "scale_authority": "v3-unified-master-orchestrator",
            "helper_scheduler": {"max_logical_helpers": self.helpers.MAX_LOGICAL_HELPERS, "max_active_workers": self.helpers.MAX_ACTIVE_WORKERS, "activation": "bounded-adaptive"},
            "skills": self.orchestrator.skills.names(),
            "tools": self.orchestrator.tools.names(),
            "tool_catalog": self.tool_catalog(),
            "tool_health": self.tool_health(),
            "tool_health_gate": self.tool_health_gate(),
            "self_learning": self.self_learning_snapshot(),
            "v3_execution": self.v3.snapshot(),
            "providers": self.orchestrator.providers.names(),
            "capabilities": self.capabilities.names(),
            "capability_manifest": self.capabilities.snapshot(),
            "memory_scope": "owner/profile/session",
            "memory_persistence": persistence,
            "reasoning_storage": "high-level-summary-only",
            "evidence": "credential-redacted",
            "v3_bridge": self.bridge.snapshot(),
        }
