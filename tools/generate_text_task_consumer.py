from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "research-os-generate-text-task/v1"
MAX_TASK_BYTES = 64 * 1024
MAX_TEXT_BYTES = 32 * 1024
MAX_TASKS = 100
_ALLOWED_KEYS = {"schema", "task_id", "owner_id", "text", "stack", "platform"}
_ALLOWED_STACKS = {
    "flutter-dart", "python", "nodejs", "dotnet", "rust", "go",
    "native-apple", "windows", "web", "android", "linux", "custom",
}
_ALLOWED_PLATFORMS = {"android", "ios", "macos", "windows", "linux", "web", "custom"}


class TextTaskError(ValueError):
    pass


@dataclass(frozen=True)
class GenerateTextTask:
    task_id: str
    owner_id: str
    text: str
    stack: str | None = None
    platform: str | None = None
    source_sha256: str = ""

    def intent(self) -> dict[str, object]:
        """Return a deterministic intent envelope; never execute or dispatch it."""
        payload: dict[str, object] = {
            "schema": SCHEMA,
            "intent": "generate.text",
            "task_id": self.task_id,
            "owner_id": self.owner_id,
            "text": self.text,
        }
        if self.stack is not None:
            payload["stack"] = self.stack
        if self.platform is not None:
            payload["platform"] = self.platform
        return payload


class GenerateTextTaskConsumer:
    """Read-only boundary from stored text tasks to Generate intents.

    The consumer validates and normalizes persisted task input. It does not call
    GitHub, execute workflows, create branches, mutate main, or invoke tools.
    A later dispatcher may consume the returned intent explicitly.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def consume_file(self, path: str | Path) -> GenerateTextTask:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise TextTaskError("task path escapes consumer root") from exc
        if not candidate.is_file():
            raise TextTaskError("task file does not exist")
        raw = candidate.read_bytes()
        if len(raw) > MAX_TASK_BYTES:
            raise TextTaskError(f"task exceeds {MAX_TASK_BYTES} bytes")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TextTaskError("task must be valid UTF-8 JSON") from exc
        task = self._validate(payload)
        digest = hashlib.sha256(raw).hexdigest()
        return GenerateTextTask(**{**task, "source_sha256": digest})

    def consume_all(self) -> tuple[GenerateTextTask, ...]:
        files = sorted(self.root.glob("*.json"))
        if len(files) > MAX_TASKS:
            raise TextTaskError(f"task collection exceeds {MAX_TASKS} files")
        return tuple(self.consume_file(path) for path in files)

    @staticmethod
    def _validate(payload: Any) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise TextTaskError("task must be a JSON object")
        unknown = set(payload) - _ALLOWED_KEYS
        if unknown:
            raise TextTaskError(f"unknown task fields: {sorted(unknown)}")
        if payload.get("schema") != SCHEMA:
            raise TextTaskError("unsupported task schema")
        task_id = GenerateTextTaskConsumer._safe_id(payload.get("task_id"), "task_id")
        owner_id = GenerateTextTaskConsumer._safe_id(payload.get("owner_id"), "owner_id")
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise TextTaskError("text is required")
        text = text.strip()
        if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
            raise TextTaskError(f"text exceeds {MAX_TEXT_BYTES} bytes")
        stack = payload.get("stack")
        if stack is not None and stack not in _ALLOWED_STACKS:
            raise TextTaskError("unsupported stack")
        platform = payload.get("platform")
        if platform is not None and platform not in _ALLOWED_PLATFORMS:
            raise TextTaskError("unsupported platform")
        return {
            "task_id": task_id,
            "owner_id": owner_id,
            "text": text,
            "stack": stack,
            "platform": platform,
        }

    @staticmethod
    def _safe_id(value: Any, field: str) -> str:
        if not isinstance(value, str):
            raise TextTaskError(f"{field} is required")
        value = value.strip()
        if not value or len(value) > 64 or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in value):
            raise TextTaskError(f"invalid {field}")
        return value


def build_dispatch_plan(task: GenerateTextTask) -> dict[str, object]:
    """Build the handoff shape expected by a future dispatcher, without dispatching."""
    return {
        "schema": SCHEMA,
        "dispatch": "deferred",
        "intent": task.intent(),
        "source_sha256": task.source_sha256,
        "execution": "not-run",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate stored Generate text tasks without executing them.")
    parser.add_argument("root", help="task directory")
    args = parser.parse_args()
    consumer = GenerateTextTaskConsumer(args.root)
    for task in consumer.consume_all():
        print(json.dumps(build_dispatch_plan(task), ensure_ascii=False, sort_keys=True))
