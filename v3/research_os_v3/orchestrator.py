from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .agents import UnifiedAgentRegistry
from .brain import BrainCore
from .execution import FactoryExecutionEngine, FactoryExecutionResult, StageHandler
from .factory import SoftwareFactory, SoftwareFactoryPlan
from .models import OrchestrationDecision, Workload
from .providers import CompletionRequest, CompletionResponse, ProviderRegistry
from .skill_runtime import NativeSkillRuntime, SkillRuntimeContext
from .skills import UnifiedSkillRegistry
from .tools import UnifiedToolRegistry


class UnifiedMasterOrchestrator:
    """Single coordination authority for Research OS V3.2 Full 10x10.

    The 10^10 tier is logical planning capacity only. Scale is selected lazily,
    while real execution remains bounded by the execution engine and explicit
    tool/skill governance.
    """

    contract = "unified-master-orchestrator-v3.2-full-10x10"

    def __init__(
        self,
        brain: BrainCore | None = None,
        providers: ProviderRegistry | None = None,
        factory: SoftwareFactory | None = None,
        skills: UnifiedSkillRegistry | None = None,
        tools: UnifiedToolRegistry | None = None,
        agents: UnifiedAgentRegistry | None = None,
    ) -> None:
        self.brain = brain or BrainCore()
        self.providers = providers or ProviderRegistry()
        self.factory = factory or SoftwareFactory()
        self.skills = skills or UnifiedSkillRegistry()
        self.tools = tools or UnifiedToolRegistry()
        self.skill_runtime = NativeSkillRuntime(self.skills)
        self.agents = agents or UnifiedAgentRegistry(skills=self.skills, tools=self.tools)

    def decide(self, workload: Workload) -> OrchestrationDecision:
        profile, demand, reason = self.brain.select_profile(workload)
        provider = self.providers.select_ready()
        return OrchestrationDecision(
            profile=profile,
            provider=provider.name,
            demand=demand,
            reason=reason,
        )

    def plan(self, workload: Workload) -> tuple[OrchestrationDecision, SoftwareFactoryPlan]:
        decision = self.decide(workload)
        return decision, self.factory.plan(decision.profile)

    def answer(
        self,
        prompt: str,
        *,
        memory_context: str | None = None,
        preferred_provider: str | None = None,
        agent_name: str | None = None,
        system_prompt: str | None = None,
    ) -> CompletionResponse:
        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")

        if agent_name:
            return self.agents.run(
                agent_name,
                cleaned,
                providers=self.providers,
                preferred_provider=preferred_provider,
                context_text=memory_context,
            )

        governed_system = (
            "You are Research OS V3.2. The Unified Master is the single coordination authority. "
            "Follow governed execution boundaries, use provided local memory only as context, "
            "never expose secrets, and never claim a tool/action ran unless its result is supplied."
            f"\n\n{self.skills.conversation_context()}"
        )
        if system_prompt:
            governed_system += f"\n\nRequested conversation guidance:\n{system_prompt.strip()}"
        if memory_context:
            governed_system += f"\n\nRelevant local memory/context:\n{memory_context}"

        return self.providers.complete(
            CompletionRequest(prompt=cleaned, system_prompt=governed_system),
            preferred=preferred_provider,
        )

    def execute_tool(
        self,
        name: str,
        arguments: dict[str, object] | None = None,
        *,
        approved: bool = False,
    ) -> dict[str, object]:
        return self.tools.execute(name, arguments, approved=approved)

    def execute_skill(
        self,
        name: str,
        text: str = "",
        *,
        arguments: dict[str, object] | None = None,
        context: SkillRuntimeContext,
    ) -> dict[str, object]:
        return self.skill_runtime.execute(name, text, arguments=arguments, context=context)

    def execute_factory(
        self,
        workload: Workload,
        *,
        handlers: Mapping[str, StageHandler],
        release_inputs: Mapping[str, object] | None = None,
        evidence_path: Path | None = None,
        hard_concurrency_limit: int = 64,
    ) -> FactoryExecutionResult:
        decision, plan = self.plan(workload)
        engine = FactoryExecutionEngine(
            hard_concurrency_limit=hard_concurrency_limit,
        )
        return engine.execute(
            workload=workload,
            decision=decision,
            plan=plan,
            handlers=handlers,
            release_inputs=release_inputs,
            evidence_path=evidence_path,
        )
