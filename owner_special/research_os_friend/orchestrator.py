from __future__ import annotations

from .brain import FriendBrain
from .context import FriendContext
from .evidence import EvidenceRecorder
from .identity import OwnerIdentity
from .memory import ScopedMemory
from .models import FriendRequest, FriendResponse
from .policy import OwnerPolicy
from .providers import ProviderRouter
from .reasoning import DecisionPlanner
from .skills import SkillRegistry
from .tools import ToolRegistry


class FriendOrchestrator:
    def __init__(
        self,
        *,
        owner: OwnerIdentity,
        brain: FriendBrain,
        planner: DecisionPlanner,
        skills: SkillRegistry,
        tools: ToolRegistry,
        providers: ProviderRouter,
        memory: ScopedMemory,
        policy: OwnerPolicy,
        evidence: EvidenceRecorder,
    ) -> None:
        self.owner = owner
        self.brain = brain
        self.planner = planner
        self.skills = skills
        self.tools = tools
        self.providers = providers
        self.memory = memory
        self.policy = policy
        self.evidence = evidence

    def handle(self, request: FriendRequest) -> FriendResponse:
        self.policy.authorize_request(self.owner, request)
        selected_skills = self.skills.resolve(request.requested_skills)
        selected_tools = self.tools.resolve(request.requested_tools)
        for tool in selected_tools:
            self.policy.authorize_tool(self.owner, request, tool.name)

        context = FriendContext.build(self.owner, request, self.memory)
        scale = self.brain.select_scale(request)
        decision = self.planner.plan(
            request,
            scale=scale,
            skills=tuple(skill.name for skill in selected_skills),
            tools=tuple(tool.name for tool in selected_tools),
        )

        skill_outputs = tuple(self.skills.run(skill, request.text) for skill in selected_skills)
        tool_outputs = tuple(tool.handler(request.text) for tool in selected_tools)
        provider = self.providers.primary()
        provider_context = tuple(item.text for item in context.memories) + skill_outputs + tool_outputs
        answer = provider.complete(prompt=request.text, context=provider_context)

        self.memory.remember(
            owner_id=request.owner_id,
            profile_id=request.profile_id,
            session_id=request.session_id,
            kind="request",
            text=request.text,
        )
        self.memory.remember(
            owner_id=request.owner_id,
            profile_id=request.profile_id,
            session_id=request.session_id,
            kind="response",
            text=answer,
        )
        evidence_id = self.evidence.record(
            owner_id=request.owner_id,
            profile_id=request.profile_id,
            session_id=request.session_id,
            event="friend-response",
            data={
                "scale": decision.scale.value,
                "capacity": decision.maximum_leaf_capacity,
                "skills": list(decision.selected_skills),
                "tools": list(decision.selected_tools),
                "provider": provider.name,
                "summary": decision.summary,
            },
        )
        memory_items = len(
            self.memory.recall(
                owner_id=request.owner_id,
                profile_id=request.profile_id,
                session_id=request.session_id,
            )
        )
        return FriendResponse(
            text=answer,
            decision=decision,
            provider=provider.name,
            memory_items=memory_items,
            evidence_id=evidence_id,
            metadata={
                "edition": self.owner.edition,
                "owner": self.owner.owner_id,
                "capabilities": self.brain.capabilities_for(request),
            },
        )
