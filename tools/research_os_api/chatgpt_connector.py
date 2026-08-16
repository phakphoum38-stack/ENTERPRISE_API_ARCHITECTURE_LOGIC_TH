from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatGPTConnectorConfig:
    """Configuration for the Research OS -> ChatGPT control layer.

    API credentials are backend-only and must be supplied through environment
    variables or a secret manager. Nothing secret is persisted in source code.
    """

    model: str
    api_key_configured: bool
    base_url: str

    @classmethod
    def from_environment(cls) -> "ChatGPTConnectorConfig":
        return cls(
            model=os.environ.get("OPENAI_MODEL", "gpt-5.6"),
            api_key_configured=bool(os.environ.get("OPENAI_API_KEY")),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )

    def dashboard(self) -> dict:
        return {
            "hub": "chatgpt",
            "connected": self.api_key_configured,
            "model": self.model,
            "base_url": self.base_url,
            "credentials": "backend_only",
        }


def get_chatgpt_connector_dashboard() -> dict:
    return ChatGPTConnectorConfig.from_environment().dashboard()
