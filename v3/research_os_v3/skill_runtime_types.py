from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MemorySearch = Callable[[str, int], list[dict[str, object]]]
MemoryAdd = Callable[[str, tuple[str, ...]], dict[str, object]]
ProviderComplete = Callable[[str, str | None], dict[str, object]]
ProviderSnapshot = Callable[[], list[dict[str, object]]]
AgentRun = Callable[[str, str], dict[str, object]]
AgentSnapshot = Callable[[], list[dict[str, object]]]
ToolRun = Callable[[str, dict[str, object], bool], dict[str, object]]
FactoryPlan = Callable[[int], dict[str, object]]


@dataclass(frozen=True)
class SkillRuntimeContext:
    user_id: str
    profile_id: str
    user_data_root: Path
    repository_root: Path
    approved: bool = False
    memory_search: MemorySearch | None = None
    memory_add: MemoryAdd | None = None
    provider_complete: ProviderComplete | None = None
    provider_snapshot: ProviderSnapshot | None = None
    agent_run: AgentRun | None = None
    agent_snapshot: AgentSnapshot | None = None
    tool_run: ToolRun | None = None
    factory_plan: FactoryPlan | None = None
