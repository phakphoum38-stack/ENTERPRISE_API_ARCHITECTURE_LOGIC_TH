from __future__ import annotations

import os
from typing import Protocol


class SecretSource(Protocol):
    def get(self, name: str) -> str | None: ...


class EnvironmentSecretSource:
    """Read secrets from process environment without exposing them in contracts."""

    def get(self, name: str) -> str | None:
        value = os.environ.get(name)
        return value if value else None
