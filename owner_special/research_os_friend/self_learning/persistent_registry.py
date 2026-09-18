from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .models import LearnedSkillCandidate
from .registry import LearnedSkillRegistry


class PersistentLearnedSkillRegistry:
    """Atomic JSON persistence layered over the existing learned-skill registry."""

    FORMAT_VERSION = 1

    def __init__(self, path: str | Path, registry: LearnedSkillRegistry | None = None) -> None:
        self.path = Path(path)
        self.registry = registry or LearnedSkillRegistry()

    def load(self) -> tuple[LearnedSkillCandidate, ...]:
        if not self.path.exists():
            return ()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("format_version") != self.FORMAT_VERSION:
            raise ValueError("unsupported learned-skill persistence format")
        records = payload.get("skills")
        if not isinstance(records, list):
            raise ValueError("learned-skill persistence requires a skills list")
        loaded: list[LearnedSkillCandidate] = []
        for raw in records:
            candidate = self._decode(raw)
            if candidate.status != "approved":
                raise ValueError("persistent registry may contain approved skills only")
            existing = self.registry.get(candidate.name)
            if existing is not None and existing != candidate:
                raise ValueError("conflicting learned-skill record")
            if existing is None:
                self.registry.promote(candidate)
            loaded.append(candidate)
        return tuple(loaded)

    def save(self) -> None:
        records = [self._encode(skill) for skill in self.registry.snapshot()]
        payload = {"format_version": self.FORMAT_VERSION, "skills": records}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    @staticmethod
    def _encode(skill: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": str(skill["name"]),
            "goal": str(skill["goal"]),
            "procedure": list(skill["procedure"]),
            "evidence": list(skill["evidence"]),
            "confidence": float(skill["confidence"]),
            "status": str(skill["status"]),
            "version": int(skill["version"]),
            "metadata": dict(skill["metadata"]),
        }

    @staticmethod
    def _decode(raw: Any) -> LearnedSkillCandidate:
        if not isinstance(raw, dict):
            raise ValueError("learned-skill record must be an object")
        procedure = raw.get("procedure")
        evidence = raw.get("evidence")
        metadata = raw.get("metadata", {})
        if not isinstance(procedure, list) or not isinstance(evidence, list) or not isinstance(metadata, dict):
            raise ValueError("malformed learned-skill record")
        return LearnedSkillCandidate(
            name=str(raw.get("name", "")),
            goal=str(raw.get("goal", "")),
            procedure=tuple(str(item) for item in procedure),
            evidence=tuple(str(item) for item in evidence),
            confidence=float(raw.get("confidence", 0.0)),
            status=str(raw.get("status", "candidate")),
            version=int(raw.get("version", 1)),
            metadata={str(key): str(value) for key, value in metadata.items()},
        )
