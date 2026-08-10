from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class AgentRole(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    API = "api"
    TEST = "test"
    SECURITY = "security"
    DOCS = "docs"
    BUILD = "build"
    MIGRATION = "migration"


DEFAULT_ROLES: tuple[AgentRole, ...] = tuple(AgentRole)


@dataclass(frozen=True)
class FactoryAgent:
    version: str
    role: AgentRole

    @property
    def agent_id(self) -> str:
        return f"{self.version}:{self.role.value}"


@dataclass
class VersionFactory:
    version: str
    repository_root: Path
    branch: str | None = None
    agents: tuple[FactoryAgent, ...] = field(init=False)

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("version must not be empty")
        self.agents = tuple(FactoryAgent(self.version, role) for role in DEFAULT_ROLES)

    @property
    def namespace(self) -> str:
        return f"factory/{self.version}"

    @property
    def worktree_root(self) -> Path:
        return self.repository_root / ".factory_state" / self.version

    def owns_path(self, path: Path) -> bool:
        """Return True only for paths inside this factory's isolated runtime workspace."""
        try:
            path.resolve().relative_to(self.worktree_root.resolve())
            return True
        except ValueError:
            return False

    def agent_ids(self) -> tuple[str, ...]:
        return tuple(agent.agent_id for agent in self.agents)


class MasterOrchestrator:
    """Registry and safety boundary for one-complete-factory-per-version execution."""

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()
        self._factories: dict[str, VersionFactory] = {}

    def register_version(self, version: str, branch: str | None = None) -> VersionFactory:
        if version in self._factories:
            return self._factories[version]
        factory = VersionFactory(version=version, repository_root=self.repository_root, branch=branch)
        self._factories[version] = factory
        return factory

    def register_versions(self, versions: Iterable[str]) -> tuple[VersionFactory, ...]:
        return tuple(self.register_version(version) for version in versions)

    def get_factory(self, version: str) -> VersionFactory:
        try:
            return self._factories[version]
        except KeyError as exc:
            raise KeyError(f"no factory registered for version {version!r}") from exc

    def versions(self) -> tuple[str, ...]:
        return tuple(self._factories)

    def assert_isolated_target(self, version: str, target: Path) -> None:
        factory = self.get_factory(version)
        if not factory.owns_path(target):
            raise PermissionError(
                f"factory {version!r} cannot mutate target outside {factory.worktree_root}"
            )
