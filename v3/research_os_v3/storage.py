from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .user_context import UserContext


@dataclass(frozen=True)
class UserDataLayout:
    """Per-user/profile mutable data boundary."""

    root: Path
    context: UserContext

    @property
    def sessions(self) -> Path:
        return self.root / "sessions"

    @property
    def database(self) -> Path:
        return self.root / "database"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def evidence(self) -> Path:
        return self.root / "evidence"

    def ensure(self) -> "UserDataLayout":
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in self.directories().values():
            directory.mkdir(parents=True, exist_ok=True)
        return self

    def directories(self) -> dict[str, Path]:
        return {
            "sessions": self.sessions,
            "database": self.database,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class DataLayout:
    """Single V3 root with isolated user/profile scopes.

    Root-level directories remain for V3 service/legacy compatibility during the
    pre-release migration. New user-owned mutable data must use ``for_user``.
    """

    root: Path

    @classmethod
    def from_environment(cls) -> "DataLayout":
        configured = os.environ.get("RESEARCH_OS_V3_DATA_DIR")
        if configured:
            return cls(Path(configured).expanduser().resolve())

        if os.name == "nt":
            program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
            return cls((Path(program_data) / "ResearchOSV3").resolve())

        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            return cls((Path(xdg_data_home).expanduser() / "research-os-v3").resolve())
        return cls((Path.home() / ".local" / "share" / "research-os-v3").resolve())

    @property
    def sessions(self) -> Path:
        return self.root / "sessions"

    @property
    def database(self) -> Path:
        return self.root / "database"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def evidence(self) -> Path:
        return self.root / "evidence"

    @property
    def users(self) -> Path:
        return self.root / "users"

    def for_user(self, context: UserContext) -> UserDataLayout:
        scoped_root = self.users / context.user_id / "profiles" / context.profile_id
        users_root = self.users.resolve()
        resolved = scoped_root.resolve()
        if resolved != users_root and users_root not in resolved.parents:
            raise ValueError("user data scope escaped the configured users root")
        return UserDataLayout(root=resolved, context=context)

    def ensure(self) -> "DataLayout":
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in (
            self.sessions,
            self.database,
            self.artifacts,
            self.logs,
            self.evidence,
            self.users,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self

    def directories(self) -> dict[str, Path]:
        # Preserve the legacy service-facing contract while user-owned data is
        # addressed explicitly through ``users`` / ``for_user``.
        return {
            "sessions": self.sessions,
            "database": self.database,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "evidence": self.evidence,
        }
