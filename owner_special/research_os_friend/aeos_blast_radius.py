"""Deterministic dependency blast-radius calculation for AEOS."""
from __future__ import annotations

from dataclasses import dataclass


class BlastRadiusError(ValueError):
    """Raised for invalid dependency topology."""


@dataclass(frozen=True)
class BlastRadius:
    root: str
    affected: tuple[str, ...]
    direct_count: int
    transitive_count: int
    risk: str


def calculate_blast_radius(*, root: str, dependencies: dict[str, tuple[str, ...]]) -> BlastRadius:
    if not isinstance(root, str) or not root:
        raise BlastRadiusError("root required")
    if not isinstance(dependencies, dict):
        raise BlastRadiusError("dependencies must be a dict")
    for node, deps in dependencies.items():
        if not isinstance(node, str) or not node or not isinstance(deps, tuple) or len(set(deps)) != len(deps):
            raise BlastRadiusError("invalid dependency graph")
        if any(not isinstance(dep, str) or not dep for dep in deps):
            raise BlastRadiusError("invalid dependency node")
    reverse: dict[str, set[str]] = {}
    for node, deps in dependencies.items():
        for dep in deps:
            reverse.setdefault(dep, set()).add(node)
    seen: set[str] = set()
    frontier = sorted(reverse.get(root, set()))
    direct = len(frontier)
    while frontier:
        node = frontier.pop(0)
        if node in seen:
            continue
        seen.add(node)
        frontier.extend(sorted(reverse.get(node, set()) - seen))
    affected = tuple(sorted(seen))
    total = len(affected)
    risk = "CRITICAL" if total >= 20 else "HIGH" if total >= 10 else "MEDIUM" if total >= 3 else "LOW"
    return BlastRadius(root, affected, direct, total, risk)
