from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .agent_runtime import AgentRun, AgentRuntime
from .agent_trace_store import PersistentAgentTraceStore
from .approval import ApprovalGate, ApprovalRecord, ApprovalState
from .approval_store import PersistentApprovalStore
from .brain import FriendBrain
from .capabilities import CapabilityRegistry, install_friend_complete_capabilities
from .catalog import install_builtin_skills, install_builtin_tools
from .evidence import EvidenceRecorder
from .helpers import HelperScheduler
from .identity import OwnerIdentity
from .learning import LearningRecord, PersistentLearningStore
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
    learning_store: PersistentLearningStore | None = None
    agent_runtime: AgentRuntime | None = None
    agent_trace_store: PersistentAgentTraceStore | None = None
    approval_store: PersistentApprovalStore | None = None
    source_commit: str = ""

    @staticmethod
    def _source_commit(repository_root: Path) -> str:
        for key in ("RESEARCH_OS_SOURCE_SHA", "GITHUB_SHA"):
            value = os.environ.get(key, "").strip()
            if value:
                return value
        build_info_candidates = (
            repository_root / "RESEARCH_OS_BUILD_INFO.txt",
            repository_root / "owner_special" / "RESEARCH_OS_BUILD_INFO.txt",
        )
        for candidate in build_info_candidates:
            if not candidate.is_file():
                continue
            for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.lower().startswith("desktop commit:"):
                    value = line.split(":", 1)[1].strip()
                    if value:
                        return value
        return ""

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
            learning_store = None
            agent_trace_store = None
            approval_store = None
        else:
            owner_root = normalized_root / "owners" / owner.owner_id
            memory = PersistentScopedMemory(owner_root / "memory" / "memory.json")
            previews = SchedulePreviewStore(normalized_root)
            if evidence_path is None:
                evidence_path = owner_root / "evidence" / "events.jsonl"
            learning_store = PersistentLearningStore(owner_root / "learning" / "learning.json")
            agent_trace_store = PersistentAgentTraceStore(owner_root / "agent" / "traces.json")
            approval_store = PersistentApprovalStore(owner_root / "agent" / "approvals.json")
        orchestrator = FriendOrchestrator(
            owner=owner,
            brain=FriendBrain(bridge),
            planner=DecisionPlanner(),
            skills=skills,
            tools=tools,
            providers=providers,
            memory=memory,
            policy=OwnerPolicy(),
            evidence=EvidenceRecorder(evidence_path),
            approval_gate=ApprovalGate(store=approval_store),
        )
        return cls(
            owner=owner,
            orchestrator=orchestrator,
            capabilities=capabilities,
            bridge=bridge,
            helpers=HelperScheduler(),
            v3=v3,
            data_root=normalized_root,
            previews=previews,
            self_learning=SelfLearningEngine(),
            learning_store=learning_store,
            agent_runtime=AgentRuntime(orchestrator, trace_store=agent_trace_store),
            agent_trace_store=agent_trace_store,
            approval_store=approval_store,
            source_commit=cls._source_commit(repo_root),
        )

    def ask(self, request: FriendRequest) -> FriendResponse:
        return self.orchestrator.handle(request)

    def run_agent(self, request: FriendRequest) -> AgentRun:
        """Run through the agent-runtime lifecycle while preserving orchestrator ownership."""
        if self.agent_runtime is None:
            self.agent_runtime = AgentRuntime(self.orchestrator, trace_store=self.agent_trace_store)
        return self.agent_runtime.run(request)

    def get_agent_run(self, run_id: str) -> AgentRun | None:
        if self.agent_runtime is None:
            self.agent_runtime = AgentRuntime(self.orchestrator, trace_store=self.agent_trace_store)
        return self.agent_runtime.get(run_id)

    def agent_runs(self) -> tuple[AgentRun, ...]:
        if self.agent_runtime is None:
            self.agent_runtime = AgentRuntime(self.orchestrator, trace_store=self.agent_trace_store)
        return self.agent_runtime.list_runs(owner_id=self.owner.owner_id)

    def inspect_tool_approval(self, request: FriendRequest, tool_name: str) -> ApprovalRecord:
        return self.orchestrator.approval_gate.inspect(self.owner, request, tool_name)

    def approve_tool(self, request: FriendRequest, tool_name: str, reason: str = "") -> ApprovalRecord:
        return self.orchestrator.approval_gate.approve(self.owner, request, tool_name, reason=reason)

    def deny_tool(self, request: FriendRequest, tool_name: str, reason: str = "") -> ApprovalRecord:
        return self.orchestrator.approval_gate.deny(self.owner, request, tool_name, reason=reason)

    def tool_approvals(self) -> tuple[ApprovalRecord, ...]:
        return self.orchestrator.approval_gate.list(owner_id=self.owner.owner_id)

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
        approved = self.self_learning.learn(candidate)
        if approved is None or self.learning_store is None:
            return approved
        if not self.source_commit:
            raise RuntimeError("learning persistence requires a canonical source commit")

        payload = {
            "owner_id": self.owner.owner_id,
            "skill_id": approved.name,
            "goal": approved.goal,
            "procedure": approved.procedure,
            "evidence": approved.evidence,
            "confidence": approved.confidence,
        }
        record_id = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        record = LearningRecord(
            record_id=record_id,
            owner_id=self.owner.owner_id,
            skill_id=approved.name,
            trigger="self_learning",
            decision_source="skill_promotion_gate",
            tools_used=(),
            source_commit=self.source_commit,
            source_workflow_run=os.environ.get("GITHUB_RUN_ID", "").strip(),
            changed_files=tuple(str(item) for item in approved.metadata.get("changed_files", ())),
            validation_result="validated",
            pr_reference=os.environ.get("GITHUB_PR_NUMBER", "").strip(),
            verification_timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=approved.confidence,
            evidence=tuple(approved.evidence),
        )
        try:
            self.learning_store.add(record)
        except ValueError as exc:
            if not str(exc).startswith("duplicate learning record"):
                raise
            return approved
        self.learning_store.promote(record.record_id, "validated", evidence=tuple(approved.evidence))
        self.learning_store.promote(record.record_id, "reusable", evidence=tuple(approved.evidence))
        return approved

    def self_learning_snapshot(self) -> dict[str, object]:
        """Expose learning state without exposing or mutating the core skill registry."""
        if self.self_learning is None:
            self.self_learning = SelfLearningEngine()
        snapshot = dict(self.self_learning.snapshot())
        if self.learning_store is None:
            snapshot.update({"persistence": "disabled", "persistent_records": 0, "persistent_reusable": 0})
        else:
            snapshot.update(
                {
                    "persistence": "owner-scoped-disk",
                    "persistent_records": self.learning_store.count(),
                    "persistent_reusable": len(self.learning_store.reusable(owner_id=self.owner.owner_id)),
                    "source_commit": self.source_commit,
                }
            )
        return snapshot

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
        approvals = self.tool_approvals()
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
            "tool_approvals": {
                "states": {state.value: sum(1 for item in approvals if item.state is state) for state in ApprovalState},
                "owner_scoped": True,
                "persistence": "owner-scoped-disk" if self.approval_store is not None else "in-process",
                "side_effect_gate": "ApprovalGate",
            },
            "self_learning": self.self_learning_snapshot(),
            "agent_runtime": {
                "enabled": self.agent_runtime is not None,
                "trace": "owner-scoped durable immutable events" if self.agent_trace_store is not None else "in-process immutable events",
                "persistence": "owner-scoped-disk" if self.agent_trace_store is not None else "disabled",
                "orchestrator_authority": "FriendOrchestrator",
                "runs": len(self.agent_runs()),
            },
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