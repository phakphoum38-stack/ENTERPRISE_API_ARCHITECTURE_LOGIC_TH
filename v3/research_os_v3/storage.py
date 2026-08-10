from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataLayout:
    """Single ownership boundary for mutable V3 service data."""

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

    def ensure(self) -> "DataLayout":
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in (
            self.sessions,
            self.database,
            self.artifacts,
            self.logs,
            self.evidence,
        ):
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
