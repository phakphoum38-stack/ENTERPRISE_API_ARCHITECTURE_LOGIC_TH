#!/usr/bin/env python3
"""Research OS AI Brain runtime composition.

This is the composition root for Brain Core slice 1. It attaches the existing
core AgentRegistry plus the isolated 12-agent Brain engineering team to the
provider-neutral Brain Core without changing the frozen RC1 runtime.
"""

from __future__ import annotations

from typing import Any, Mapping

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory
from v2_brain_team import brain_team_dashboard, register_brain_team


class BrainRuntime:
    def __init__(
        self,
        *,
        registry: AgentRegistry | None = None,
        working_memory: WorkingMemory | None = None,
        ledger: ActivityLedger | None = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        register_brain_team(self.registry)
        self.brain = ResearchOSBrain(
            registry=self.registry,
            working_memory=working_memory,
            ledger=ledger,
        )

    def introspect(self) -> dict[str, Any]:
        return {
            "brain": self.brain.introspect(),
            "team": brain_team_dashboard(self.registry),
        }

    def plan(
        self,
        objective: str,
        *,
        session_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = self.brain.plan(objective, session_id=session_id, context=context)
        return {
            "plan": plan,
            "team": brain_team_dashboard(self.registry),
        }


BRAIN_RUNTIME = BrainRuntime()
