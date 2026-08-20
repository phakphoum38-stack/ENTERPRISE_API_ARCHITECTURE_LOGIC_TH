from __future__ import annotations

from .models import ConversationTurn


class NaturalConversationPolicy:
    """Provider-neutral response policy: concise, contextual, non-template-like by default."""

    def __init__(self, max_context_turns: int = 12) -> None:
        if max_context_turns < 1:
            raise ValueError("max_context_turns must be positive")
        self.max_context_turns = max_context_turns

    def context(self, turns: tuple[ConversationTurn, ...]) -> tuple[ConversationTurn, ...]:
        return turns[-self.max_context_turns :]

    def normalize(self, text: str) -> str:
        value = " ".join(text.split()).strip()
        if not value:
            raise ValueError("response cannot be empty")
        # Avoid mechanically repeated assistant boilerplate while preserving user wording.
        for prefix in ("As an AI,", "As an AI assistant,", "Certainly! "):
            if value.startswith(prefix):
                value = value[len(prefix):].lstrip()
        return value
