#!/usr/bin/env python3
"""Bounded, self-auditing discovery infrastructure for the Platform registry.

The engine reuses the existing Platform Virtual Workspace registry as its source
of truth. It adds no second registry, scheduler, queue, authority, or runtime.
Discovery is location-oriented and fail-closed: same-level peers are checked
before descending, ambiguity stops creation, and every run emits a proof.
"""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from threading import Event, Lock
from typing import Any, Callable, Iterable, Mapping, Sequence


class DiscoveryScope(str, Enum):
    INTERNAL = 'INTERNAL'
    EXTERNAL = 'EXTERNAL'


class DiscoveryAuthority(str, Enum):
    SYSTEM = 'SYSTEM'
    OBSERVATION_ONLY = 'OBSERVATION_ONLY'


class DiscoveryResult(str, Enum):
    FOUND = "FOUND"
    FOUND_AT = "FOUND_AT"
    ABSENT_FROM_SCOPE = "ABSENT_FROM_SCOPE"
    ROOT_UNRESOLVED = "ROOT_UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    TIMEOUT = "TIMEOUT"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class DiscoveryHalt(RuntimeError):
    """Raised when discovery must stop without creating or guessing anything."""


@dataclass(frozen=True)
class DiscoveryBudget:
    max_time_ms: int = 60_000
    max_depth: int = 32
    max_nodes: int = 100_000
    max_workers: int = 8
    max_remote_calls: int = 128
    max_queue: int = 256

    def validate(self) -> None:
        if not 1 <= self.max_time_ms <= 300_000:
            raise ValueError("max_time_ms must be between 1 and 300000")
        if not 1 <= self.max_depth <= 256:
            raise ValueError("max_depth must be between 1 and 256")
        if not 1 <= self.max_nodes <= 10_000_000:
            raise ValueError("max_nodes out of bounds")
        if not 1 <= self.max_workers <= 64:
            raise ValueError("max_workers out of bounds")
        if not 0 <= self.max_remote_calls <= 100_000:
            raise ValueError("max_remote_calls out of bounds")
        if not 1 <= self.max_queue <= 100_000:
            raise ValueError("max_queue out of bounds")


@dataclass(frozen=True)
class DiscoveryNode:
    node_id: str
    level: int
    name: str
    kind: str
    parent_id: str | None = None
    virtual_space: str | None = None
    root_id: str | None = None
    capability: str | None = None
    version: str | None = None
    fingerprint: str | None = None
    references: tuple[str, ...] = ()
    active: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)
    scope: DiscoveryScope = DiscoveryScope.INTERNAL
    authority: DiscoveryAuthority = DiscoveryAuthority.SYSTEM

    def structural_fingerprint(self) -> str:
        payload = {
            "kind": self.kind,
            "name": self.name.casefold(),
            "capability": (self.capability or "").casefold(),
            "parent_id": self.parent_id,
            "children_shape": self.metadata.get("children_shape", []),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class DiscoveryCandidate:
    node_id: str
    level: int
    score: float
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveryProof:
    discovery_id: str
    result: DiscoveryResult
    virtual_space: str | None
    root_id: str | None
    target: str
    levels_examined: tuple[int, ...]
    candidates: tuple[str, ...]
    nodes_examined: int
    peers_examined: int
    remote_calls: int
    cache_hit: bool
    index_hit: bool
    latency_ms: int
    reason: str
    evidence: tuple[str, ...] = ()
    source_scope: DiscoveryScope = DiscoveryScope.INTERNAL
    authority: DiscoveryAuthority = DiscoveryAuthority.SYSTEM

    def as_dict(self) -> dict[str, Any]:
        return {
            "discovery_id": self.discovery_id,
            "result": self.result.value,
            "virtual_space": self.virtual_space,
            "root_id": self.root_id,
            "target": self.target,
            "levels_examined": list(self.levels_examined),
            "candidates": list(self.candidates),
            "nodes_examined": self.nodes_examined,
            "peers_examined": self.peers_examined,
            "remote_calls": self.remote_calls,
            "cache_hit": self.cache_hit,
            "index_hit": self.index_hit,
            "latency_ms": self.latency_ms,
            "reason": self.reason,
            "evidence": list(self.evidence),
            "source_scope": self.source_scope.value,
            "authority": self.authority.value,
        }


@dataclass(frozen=True)
class DiscoveryResponse:
    result: DiscoveryResult
    node_id: str | None
    proof: DiscoveryProof


class DiscoveryEmergencyStop(Exception):
    """Emergency stop used when bounded-search safety invariants are violated."""


class Backpressure:
    """Small admission controller; it never becomes a second task queue."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._active = 0
        self._lock = Lock()

    def acquire(self) -> bool:
        with self._lock:
            if self._active >= self.capacity:
                return False
            self._active += 1
            return True

    def release(self) -> None:
        with self._lock:
            if self._active:
                self._active -= 1


class DiscoveryIndex:
    """Rebuildable index over the canonical registry projection."""

    def __init__(self, nodes: Iterable[DiscoveryNode] = ()) -> None:
        self._nodes: dict[str, DiscoveryNode] = {}
        self._by_parent: dict[str | None, list[str]] = {}
        self._by_capability: dict[str, list[str]] = {}
        self._by_fingerprint: dict[str, list[str]] = {}
        self._lock = Lock()
        self.rebuild(nodes)

    def rebuild(self, nodes: Iterable[DiscoveryNode]) -> None:
        fresh = list(nodes)
        by_parent: dict[str | None, list[str]] = {}
        by_capability: dict[str, list[str]] = {}
        by_fingerprint: dict[str, list[str]] = {}
        mapping: dict[str, DiscoveryNode] = {}
        for node in fresh:
            if node.node_id in mapping:
                raise ValueError(f"duplicate_node_id:{node.node_id}")
            mapping[node.node_id] = node
            by_parent.setdefault(node.parent_id, []).append(node.node_id)
            if node.capability:
                by_capability.setdefault(node.capability.casefold(), []).append(node.node_id)
            fp = node.fingerprint or node.structural_fingerprint()
            by_fingerprint.setdefault(fp, []).append(node.node_id)
        with self._lock:
            self._nodes = mapping
            self._by_parent = by_parent
            self._by_capability = by_capability
            self._by_fingerprint = by_fingerprint

    def get(self, node_id: str) -> DiscoveryNode | None:
        return self._nodes.get(node_id)

    def peers(self, parent_id: str | None, level: int) -> list[DiscoveryNode]:
        return [
            self._nodes[node_id]
            for node_id in self._by_parent.get(parent_id, [])
            if self._nodes[node_id].level == level
        ]

    def children(self, parent_id: str) -> list[DiscoveryNode]:
        return [self._nodes[x] for x in self._by_parent.get(parent_id, [])]

    def capability_matches(self, capability: str) -> list[DiscoveryNode]:
        return [self._nodes[x] for x in self._by_capability.get(capability.casefold(), [])]

    def fingerprint_matches(self, fingerprint: str) -> list[DiscoveryNode]:
        return [self._nodes[x] for x in self._by_fingerprint.get(fingerprint, [])]

    def nodes(self) -> list[DiscoveryNode]:
        return list(self._nodes.values())


class DiscoveryEngine:
    """Hierarchical, bounded discovery with proof and fail-closed creation guards."""

    def __init__(
        self,
        nodes: Iterable[DiscoveryNode],
        *,
        budget: DiscoveryBudget | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.budget = budget or DiscoveryBudget()
        self.budget.validate()
        self.clock = clock
        self.index = DiscoveryIndex(nodes)
        self._negative_cache: dict[tuple[str, str, str], DiscoveryProof] = {}
        self._positive_cache: dict[tuple[str, str, str], str] = {}
        self._stop = Event()
        self._backpressure = Backpressure(self.budget.max_queue)

    @staticmethod
    def authority_for(scope: DiscoveryScope) -> DiscoveryAuthority:
        return DiscoveryAuthority.SYSTEM if scope == DiscoveryScope.INTERNAL else DiscoveryAuthority.OBSERVATION_ONLY

    def resolve_scope(self, virtual_space: str | None, root_id: str | None) -> DiscoveryScope:
        if not virtual_space or not root_id:
            raise DiscoveryHalt('scope_unresolved')
        root = self.index.get(root_id)
        if root is None:
            raise DiscoveryHalt('root_unresolved')
        return root.scope

    def emergency_stop(self, reason: str = "operator_or_safety_stop") -> None:
        self._stop.set()
        self._emergency_reason = reason

    def rebuild(self, nodes: Iterable[DiscoveryNode]) -> None:
        self.index.rebuild(nodes)
        self._negative_cache.clear()
        self._positive_cache.clear()
        self._stop.clear()

    def discover(
        self,
        *,
        virtual_space: str | None,
        root_id: str | None,
        target: str,
        start_parent_id: str | None = None,
        start_level: int = 0,
        scope: DiscoveryScope | None = None,
    ) -> DiscoveryResponse:
        started = self.clock()
        discovery_id = hashlib.sha256(
            f"{virtual_space}|{root_id}|{target}|{started}".encode()
        ).hexdigest()[:16]
        levels: list[int] = []
        candidates: list[DiscoveryCandidate] = []
        nodes_examined = peers_examined = remote_calls = 0
        cache_key = (virtual_space or "", root_id or "", target.casefold())

        if self._stop.is_set():
            return self._response(
                discovery_id, DiscoveryResult.EMERGENCY_STOP, None, virtual_space, root_id,
                target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                False, False, started, getattr(self, "_emergency_reason", "stopped"),
            )

        if root_id is None or self.index.get(root_id) is None:
            return self._response(
                discovery_id, DiscoveryResult.ROOT_UNRESOLVED, None, virtual_space, root_id,
                target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                False, False, started, "root_unresolved",
            )

        if cache_key in self._positive_cache:
            node_id = self._positive_cache[cache_key]
            return self._response(
                discovery_id, DiscoveryResult.FOUND_AT, node_id, virtual_space, root_id,
                target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                True, True, started, "positive_cache",
            )

        if cache_key in self._negative_cache:
            proof = self._negative_cache[cache_key]
            return DiscoveryResponse(DiscoveryResult.ABSENT_FROM_SCOPE, None, proof)

        target_norm = target.casefold()
        frontier = [start_parent_id or root_id]
        level = start_level

        while frontier and level <= self.budget.max_depth:
            try:
                self._check_budget(started, nodes_examined)
            except DiscoveryHalt as exc:
                return self._response(
                    discovery_id, DiscoveryResult.TIMEOUT, None, virtual_space, root_id,
                    target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                    False, True, started, str(exc),
                )

            if self._stop.is_set():
                return self._response(
                    discovery_id, DiscoveryResult.EMERGENCY_STOP, None, virtual_space, root_id,
                    target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                    False, False, started, getattr(self, "_emergency_reason", "stopped"),
                )

            levels.append(level)
            next_frontier: list[str] = []
            for parent_id in frontier:
                peers = self.index.peers(parent_id, level)
                peers_examined += len(peers)
                for node in peers:
                    nodes_examined += 1
                    if nodes_examined > self.budget.max_nodes:
                        return self._response(
                            discovery_id, DiscoveryResult.TIMEOUT, None, virtual_space, root_id,
                            target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                            False, True, started, "node_budget_exhausted",
                        )
                    score, evidence = self._score(node, target_norm)
                    if score > 0:
                        candidates.append(
                            DiscoveryCandidate(node.node_id, node.level, score, tuple(evidence))
                        )

                children = self.index.children(parent_id)
                next_frontier.extend(
                    child.node_id for child in children if child.level > level
                )

            exact = [c for c in candidates if c.level == level and c.score >= 1.0]
            if len(exact) == 1:
                node_id = exact[0].node_id
                self._positive_cache[cache_key] = node_id
                return self._response(
                    discovery_id, DiscoveryResult.FOUND_AT, node_id, virtual_space, root_id,
                    target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                    False, True, started, "same_level_exact_match",
                )
            if len(exact) > 1:
                return self._response(
                    discovery_id, DiscoveryResult.AMBIGUOUS, None, virtual_space, root_id,
                    target, levels, candidates, nodes_examined, peers_examined, remote_calls,
                    False, True, started, "multiple_same_level_matches",
                )

            frontier = sorted(set(next_frontier))
            level += 1

        result = DiscoveryResult.ABSENT_FROM_SCOPE
        proof = self._proof(
            discovery_id, result, virtual_space, root_id, target, levels, candidates,
            nodes_examined, peers_examined, remote_calls, False, True, started,
            "absent_after_bounded_hierarchical_scan",
        )
        self._negative_cache[cache_key] = proof
        return DiscoveryResponse(result, None, proof)

    def can_create(self, response: DiscoveryResponse) -> bool:
        return response.result == DiscoveryResult.ABSENT_FROM_SCOPE

    def duplicate_capabilities(self, capability: str) -> list[tuple[str, ...]]:
        matches = self.index.capability_matches(capability)
        groups: dict[str, list[str]] = {}
        for node in matches:
            fp = node.fingerprint or node.structural_fingerprint()
            groups.setdefault(fp, []).append(node.node_id)
        return [tuple(sorted(group)) for group in groups.values() if len(group) > 1]

    def duplicate_fingerprints(self, fingerprint: str) -> tuple[str, ...]:
        return tuple(sorted(n.node_id for n in self.index.fingerprint_matches(fingerprint)))

    def stale_candidates(self) -> list[str]:
        return sorted(
            n.node_id for n in self.index.nodes()
            if n.active and not n.references
        )

    def same_level_parallel_probe(
        self,
        candidates: Sequence[DiscoveryNode],
        probe: Callable[[DiscoveryNode], DiscoveryCandidate | None],
    ) -> list[DiscoveryCandidate]:
        if not candidates:
            return []
        if not self._backpressure.acquire():
            raise DiscoveryHalt("backpressure")
        try:
            results: list[DiscoveryCandidate] = []
            with ThreadPoolExecutor(max_workers=min(self.budget.max_workers, len(candidates))) as pool:
                futures = [pool.submit(probe, item) for item in candidates]
                for future in as_completed(futures):
                    if self._stop.is_set():
                        for item in futures:
                            item.cancel()
                        raise DiscoveryHalt("emergency_stop")
                    value = future.result()
                    if value:
                        results.append(value)
            return sorted(results, key=lambda x: (-x.score, x.node_id))
        finally:
            self._backpressure.release()

    def _score(self, node: DiscoveryNode, target: str) -> tuple[float, list[str]]:
        name = node.name.casefold()
        if name == target:
            return 1.0, ["exact_name"]
        if node.node_id.casefold() == target:
            return 1.0, ["exact_id"]
        if node.capability and node.capability.casefold() == target:
            return 1.0, ["exact_capability"]
        if target in name:
            return 0.5, ["name_contains"]
        return 0.0, []

    def _check_budget(self, started: float, nodes_examined: int) -> None:
        if (self.clock() - started) * 1000 >= self.budget.max_time_ms:
            raise DiscoveryHalt("time_budget_exhausted")
        if nodes_examined >= self.budget.max_nodes:
            raise DiscoveryHalt("node_budget_exhausted")

    def _response(
        self, discovery_id: str, result: DiscoveryResult, node_id: str | None,
        virtual_space: str | None, root_id: str | None, target: str,
        levels: list[int], candidates: list[DiscoveryCandidate], nodes_examined: int,
        peers_examined: int, remote_calls: int, cache_hit: bool, index_hit: bool,
        started: float, reason: str,
    ) -> DiscoveryResponse:
        try:
            proof = self._proof(
                discovery_id, result, virtual_space, root_id, target, levels, candidates,
                nodes_examined, peers_examined, remote_calls, cache_hit, index_hit, started, reason,
            )
        except DiscoveryHalt:
            proof = self._proof_unbounded(
                discovery_id, result, virtual_space, root_id, target, levels, candidates,
                nodes_examined, peers_examined, remote_calls, cache_hit, index_hit, reason,
            )
        return DiscoveryResponse(result, node_id, proof)

    def _proof(
        self,
        discovery_id: str,
        result: DiscoveryResult,
        virtual_space: str | None,
        root_id: str | None,
        target: str,
        levels: list[int],
        candidates: list[DiscoveryCandidate],
        nodes_examined: int,
        peers_examined: int,
        remote_calls: int,
        cache_hit: bool,
        index_hit: bool,
        started: float,
        reason: str,
    ) -> DiscoveryProof:
        latency_ms = int((self.clock() - started) * 1000)
        if latency_ms > self.budget.max_time_ms:
            raise DiscoveryHalt("proof_exceeded_budget")
        return DiscoveryProof(
            discovery_id,
            result,
            virtual_space,
            root_id,
            target,
            tuple(levels),
            tuple(c.node_id for c in candidates),
            nodes_examined,
            peers_examined,
            remote_calls,
            cache_hit,
            index_hit,
            latency_ms,
            reason,
            tuple(sorted({e for c in candidates for e in c.evidence})),
            scope, self.authority_for(scope),
        )

    @staticmethod
    def _proof_unbounded(
        discovery_id: str, result: DiscoveryResult, virtual_space: str | None,
        root_id: str | None, target: str, levels: list[int],
        candidates: list[DiscoveryCandidate], nodes_examined: int,
        peers_examined: int, remote_calls: int, cache_hit: bool,
        index_hit: bool, reason: str,
    ) -> DiscoveryProof:
        return DiscoveryProof(
            discovery_id, result, virtual_space, root_id, target, tuple(levels),
            tuple(c.node_id for c in candidates), nodes_examined, peers_examined,
            remote_calls, cache_hit, index_hit, 0, reason,
            tuple(sorted({e for c in candidates for e in c.evidence})),
        )


def build_nodes_from_platform_registry(registry: Mapping[str, Any], scope: DiscoveryScope = DiscoveryScope.INTERNAL) -> list[DiscoveryNode]:
    """Adapt the existing Platform registry without creating another registry."""
    nodes: list[DiscoveryNode] = []
    root = DiscoveryNode("platform-root", 0, "PLATFORM", "VIRTUAL_SPACE", root_id="platform-root", scope=scope, authority=DiscoveryEngine.authority_for(scope))
    nodes.append(root)
    for record in registry.get("records", []):
        path = str(record.get("virtual_path", ""))
        parts = [p for p in path.split("/") if p]
        parent = "platform-root"
        level = 1
        for part in parts[1:]:
            node_id = f"platform:{'/'.join(parts[:level + 1])}"
            existing = next((x for x in nodes if x.node_id == node_id), None)
            if existing is None:
                nodes.append(DiscoveryNode(
                    node_id, level, part, "WORKSPACE_LEVEL",
                    parent_id=parent, virtual_space="PLATFORM", root_id="platform-root",
                ))
            parent = node_id
            level += 1
        nodes.append(DiscoveryNode(
            record["work_id"], level, record["name"], "WORK",
            parent_id=parent, virtual_space="PLATFORM", root_id="platform-root",
            capability=record["purpose"], version=str(record.get("revision", "")) or None,
            references=tuple(record.get("source_refs", [])),
            active=record.get("status") not in {"SUPERSEDED"},
            metadata={"resolution": record.get("resolution")},
            scope=scope, authority=DiscoveryEngine.authority_for(scope),
        ))
    return nodes
