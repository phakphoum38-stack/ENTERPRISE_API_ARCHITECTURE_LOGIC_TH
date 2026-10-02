from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from tools.research_os_resource_parser import explicit_identities
from tools.research_os_resource_parser import normalize_path
from tools.research_os_resource_parser import structured_bindings

SEMANTIC_ASSURANCE_RELATIONS = frozenset({
    "VERIFIED_BY",
    "SUPPORTED_BY",
    "BOUND_TO",
    "ENFORCED_BY",
    "DISPATCHED_BY",
})

MULTI_CARDINALITY_RELATIONS = frozenset({
    "VERIFIED_BY",
    "SUPPORTED_BY",
})

SINGLE_CARDINALITY_RELATIONS = frozenset({
    "BOUND_TO",
    "ENFORCED_BY",
    "DISPATCHED_BY",
})

IDENTITY_FIELDS = (
    "contract",
    "contract_id",
    "capability_id",
    "component_id",
)

@dataclass(frozen=True)
class BindingResult:
    relation: str
    targets: tuple[str, ...]
    tier: str | None
    ambiguous: bool
    unresolved: bool
    candidates: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "relation": self.relation,
            "targets": list(self.targets),
            "tier": self.tier,
            "ambiguous": self.ambiguous,
            "unresolved": self.unresolved,
            "candidates": list(self.candidates),
        }

def contract_stem(path: str) -> str:
    name = Path(path).name.lower()
    suffixes = (
        "_contract.json",
        "_contract.yaml",
        "_contract.yml",
        "-contract.json",
        "-contract.yaml",
        "-contract.yml",
    )
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return Path(path).stem.lower()

def _structured_binding(text: str) -> dict | None:
    return structured_bindings(text)

def _explicit_path_match(candidate: str, text: str) -> bool:
    binding = _structured_binding(text)
    if not binding:
        return False
    paths = binding.get('paths', [])
    if isinstance(paths, str):
        paths = [paths]
    normalized = {
        normalize_path(str(value))
        for value in paths
        if isinstance(value, str)
    }
    return normalize_path(candidate) in normalized

def _explicit_contract_reference_match(target: str, text: str) -> bool:
    normalized = normalize_path(target)
    target_name = Path(normalized).name
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if normalized in stripped or target_name in stripped:
            return True
    return False

def _semantic_identity_match(
    target: str,
    candidate: str,
    texts: dict[str, str],
) -> bool:
    target_ids = explicit_identities(target, texts.get(target, ''))
    candidate_ids = explicit_identities(candidate, texts.get(candidate, ''))
    return bool(target_ids & candidate_ids)

def resolve_semantic_binding(
    *,
    target: str,
    relation: str,
    candidates: Iterable[str],
    texts: dict[str, str],
) -> BindingResult:
    if relation not in SEMANTIC_ASSURANCE_RELATIONS:
        raise ValueError(
            f'Unsupported semantic assurance relation: {relation}'
        )

    target = normalize_path(target)
    candidates = tuple(sorted({
        normalize_path(str(candidate))
        for candidate in candidates
        if normalize_path(str(candidate)) != target
    }))

    # Winning tier only: lower-priority tiers are never merged into it.
    explicit_path = [
        candidate
        for candidate in candidates
        if _explicit_path_match(
            candidate,
            texts.get(candidate, ''),
        )
    ]
    if explicit_path:
        winners = tuple(sorted(set(explicit_path)))
        return _result(relation, winners, 'EXPLICIT_PATH')

    explicit_reference = [
        candidate
        for candidate in candidates
        if _explicit_contract_reference_match(
            target,
            texts.get(candidate, ''),
        )
    ]
    if explicit_reference:
        winners = tuple(sorted(set(explicit_reference)))
        return _result(
            relation,
            winners,
            'EXPLICIT_CONTRACT_REFERENCE',
        )

    structured = []
    for candidate in candidates:
        binding = _structured_binding(texts.get(candidate, ''))
        if not binding:
            continue
        values = binding.get(relation)
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            continue
        normalized_values = {
            normalize_path(str(value))
            for value in values
            if isinstance(value, str)
        }
        if target in normalized_values:
            structured.append(candidate)

    if structured:
        winners = tuple(sorted(set(structured)))
        return _result(
            relation,
            winners,
            'STRUCTURED_BINDING_FIELD',
        )

    semantic = [
        candidate
        for candidate in candidates
        if _semantic_identity_match(
            target,
            candidate,
            texts,
        )
    ]
    if semantic:
        winners = tuple(sorted(set(semantic)))
        return _result(
            relation,
            winners,
            'UNIQUE_SEMANTIC_IDENTITY',
        )

    return BindingResult(
        relation=relation,
        targets=(),
        tier=None,
        ambiguous=False,
        unresolved=True,
        candidates=candidates,
    )

def _result(
    relation: str,
    winners: tuple[str, ...],
    tier: str,
) -> BindingResult:
    if relation in SINGLE_CARDINALITY_RELATIONS and len(winners) != 1:
        return BindingResult(
            relation=relation,
            targets=(),
            tier=tier,
            ambiguous=True,
            unresolved=False,
            candidates=winners,
        )
    return BindingResult(
        relation=relation,
        targets=winners,
        tier=tier,
        ambiguous=False,
        unresolved=False,
        candidates=winners,
    )
