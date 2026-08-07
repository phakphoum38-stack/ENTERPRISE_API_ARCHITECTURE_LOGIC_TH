#!/usr/bin/env python3
"""Deterministic, dependency-free memory retrieval for Research OS."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemoryHit:
    artifact_id: str
    title: str
    status: str
    path: str
    score: int
    matched_terms: list[str]
    excerpt: str


def _tokens(value: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_\-]+|[\u0E00-\u0E7F]+", value)
        if len(token.strip()) >= 2
    }


def _front_matter(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in content[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def _excerpt(content: str, terms: set[str], limit: int = 360) -> str:
    body = content
    if content.startswith("---\n"):
        end = content.find("\n---", 4)
        if end >= 0:
            body = content[end + 4 :]
    lines = [line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")]
    ranked = sorted(lines, key=lambda line: len(_tokens(line) & terms), reverse=True)
    text = " ".join(ranked[:3]) if ranked else ""
    return text[:limit]


def search_memory(directory: Path, query: str, limit: int = 5) -> list[dict[str, object]]:
    terms = _tokens(query)
    if not terms:
        return []
    hits: list[MemoryHit] = []
    for path in sorted(directory.glob("RES-*.md")):
        content = path.read_text(encoding="utf-8")
        metadata = _front_matter(content)
        title = metadata.get("title", path.stem)
        artifact_id = metadata.get("artifact_id", path.stem)
        status = metadata.get("status", "unknown")
        title_tokens = _tokens(title)
        content_tokens = _tokens(content)
        title_matches = terms & title_tokens
        content_matches = terms & content_tokens
        score = len(title_matches) * 5 + len(content_matches)
        if score <= 0:
            continue
        matched = sorted(title_matches | content_matches)
        hits.append(
            MemoryHit(
                artifact_id=artifact_id,
                title=title,
                status=status,
                path=str(path),
                score=score,
                matched_terms=matched,
                excerpt=_excerpt(content, terms),
            )
        )
    hits.sort(key=lambda item: (-item.score, item.artifact_id))
    return [asdict(item) for item in hits[: max(1, min(limit, 20))]]


def build_context(hits: list[dict[str, object]], max_chars: int = 4000) -> str:
    parts: list[str] = []
    for hit in hits:
        parts.append(
            "\n".join(
                [
                    f"Artifact: {hit['artifact_id']}",
                    f"Title: {hit['title']}",
                    f"Status: {hit['status']}",
                    f"Excerpt: {hit['excerpt']}",
                ]
            )
        )
    return "\n\n".join(parts)[:max_chars]
