#!/usr/bin/env python3
"""Local-first storage paths for Research OS.

Set RESEARCH_OS_DATA_DIR to a durable folder on the machine running the API.
The module does not store secrets; it only owns user data paths.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    configured = os.getenv("RESEARCH_OS_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (ROOT / ".research_os_data").resolve()


def artifacts_dir() -> Path:
    return data_root() / "artifacts"


def sessions_dir() -> Path:
    return data_root() / "sessions"


def database_dir() -> Path:
    return data_root() / "database"


def backups_dir() -> Path:
    return data_root() / "backups"


def conversation_store_path() -> Path:
    explicit = os.getenv("RESEARCH_OS_CONVERSATION_STORE", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return sessions_dir() / "conversations.json"


def ensure_layout() -> dict[str, str]:
    paths = {
        "root": data_root(),
        "artifacts": artifacts_dir(),
        "sessions": sessions_dir(),
        "database": database_dir(),
        "backups": backups_dir(),
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return {name: str(path) for name, path in paths.items()}
