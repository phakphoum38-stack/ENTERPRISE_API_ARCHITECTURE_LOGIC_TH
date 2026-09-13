from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class CopilotChatError(RuntimeError):
    """Raised when the enterprise Copilot Chat bridge cannot complete."""


class CopilotChatClient:
    """Minimal stdlib client for an enterprise Copilot Chat-compatible gateway."""

    def __init__(
        self,
        *,
        api_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_url = str(
            api_url or os.getenv("RESEARCH_OS_COPILOT_API_URL") or ""
        ).strip()
        self.api_key = str(
            api_key or os.getenv("RESEARCH_OS_COPILOT_API_KEY") or ""
        ).strip()
        self.model = str(model or os.getenv("RESEARCH_OS_COPILOT_MODEL") or "").strip()
        self.timeout = float(
            timeout
            if timeout is not None
            else os.getenv("RESEARCH_OS_COPILOT_TIMEOUT", "30")
        )
        if not self.api_url:
            raise CopilotChatError(
                "RESEARCH_OS_COPILOT_API_URL is required for Copilot Chat integration"
            )

    def chat(
        self,
        *,
        messages: list[dict[str, str]],
        context: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model": (model or self.model or None),
            "messages": messages,
            "context": context,
            "metadata": metadata or {},
        }
        request = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                value = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise CopilotChatError(
                f"Copilot Chat gateway HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise CopilotChatError(
                f"Copilot Chat gateway unavailable: {exc.reason}"
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CopilotChatError("Copilot Chat gateway returned invalid JSON") from exc

        if not isinstance(value, dict):
            raise CopilotChatError("Copilot Chat gateway returned an invalid payload")

        text = self._extract_text(value)
        if not text:
            raise CopilotChatError("Copilot Chat gateway returned no assistant reply")

        return {
            "reply": text,
            "model": value.get("model") or model or self.model or "copilot-chat",
            "raw": value,
        }

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if self.api_key:
            headers["Authorization"] = f"******"
        return headers

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        for key in ("reply", "text", "content", "output_text", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        choices = payload.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                    if isinstance(content, list):
                        parts = [
                            str(item.get("text", "")).strip()
                            for item in content
                            if isinstance(item, dict)
                        ]
                        joined = "\n".join(part for part in parts if part)
                        if joined:
                            return joined
        return ""
