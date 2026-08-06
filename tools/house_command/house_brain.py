#!/usr/bin/env python3
"""Deterministic House Brain v0.1.

Reads project-owned records and returns a structured, non-generative house status.
The owner remains the final decision maker; this module only observes and suggests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class HouseStatus:
    health: str
    score: int
    required_files_present: int
    required_files_total: int
    knowledge_artifacts: int
    missing: list[str]
    next_focus: list[str]
    motto: str = "บ้านของเรา…ดีขึ้นกว่าเมื่อวาน"


REQUIRED_FILES = (
    "house/HOUSE_STRUCTURE.md",
    "house/MISSION_REPORT.md",
    "house/HOUSE_LOG.md",
    "tools/research_curator/curator.py",
    "tools/research_os_api/server.py",
    ".github/workflows/research-curator-validate.yml",
    ".github/workflows/house-command.yml",
)


def analyze(root: Path) -> dict[str, object]:
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    present = len(REQUIRED_FILES) - len(missing)
    artifact_dir = root / "research" / "artifacts"
    artifacts = len([path for path in artifact_dir.glob("RES-*.md") if path.is_file()]) if artifact_dir.exists() else 0

    score = round((present / len(REQUIRED_FILES)) * 80) + min(artifacts * 5, 20)
    if missing:
        health = "needs-attention"
    elif score >= 90:
        health = "healthy"
    else:
        health = "building"

    next_focus: list[str] = []
    if missing:
        next_focus.append("restore-required-files")
    if artifacts == 0:
        next_focus.append("capture-first-knowledge-artifact")
    next_focus.extend(["entrance", "ai-gateway", "knowledge-engine"])

    status = HouseStatus(
        health=health,
        score=min(score, 100),
        required_files_present=present,
        required_files_total=len(REQUIRED_FILES),
        knowledge_artifacts=artifacts,
        missing=missing,
        next_focus=next_focus,
    )
    return asdict(status)
