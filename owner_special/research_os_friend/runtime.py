from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .brain import FriendBrain
from .catalog import install_builtin_skills, install_builtin_tools
from .evidence import EvidenceRecorder
from .identity import OwnerIdentity
from .memory import ScopedMemory
from .models import FriendRequest, FriendResponse
from .orchestrator import FriendOrchestrator
from .policy import OwnerPolicy
from .providers import MockProvider, ProviderRouter
from .reasoning import DecisionPlanner
from .skills import SkillRegistry
from .tools import ToolRegistry


@dataclass
class FriendRuntime:
    owner: OwnerIdentity
    orchestrator: FriendOrchestrator

    @classmethod
    def create_owner_special(
        cls,
        owner_id: str,
        *,
        display_name: str = "Owner",
        evidence_path: Path | None = None,
    ) -> "FriendRuntime":
        owner = OwnerIdentity(owner_id=owner_id, display_name=display_name)
        skills = install_builtin_skills(SkillRegistry())
        tools = install_builtin_tools(ToolRegistry())
        providers = ProviderRouter()
        providers.register(MockProvider())
        orchestrator = FriendOrchestrator(
            owner=owner,
            brain=FriendBrain(),
            planner=DecisionPlanner(),
            skills=skills,
            tools=tools,
            providers=providers,
            memory=ScopedMemory(),
            policy=OwnerPolicy(),
            evidence=EvidenceRecorder(evidence_path),
        )
        return cls(owner=owner, orchestrator=orchestrator)

    def ask(self, request: FriendRequest) -> FriendResponse:
        return self.orchestrator.handle(request)

    def architecture(self) -> dict[str, object]:
        return {
            "edition": self.owner.edition,
            "owner_id": self.owner.owner_id,
            "brain_profiles": {"1^3": 1, "3^3": 27, "6^3": 216, "6^6": 46656},
            "skills": self.orchestrator.skills.names(),
            "tools": self.orchestrator.tools.names(),
            "providers": self.orchestrator.providers.names(),
            "memory_scope": "owner/profile/session",
            "reasoning_storage": "high-level-summary-only",
            "evidence": "credential-redacted",
        }
