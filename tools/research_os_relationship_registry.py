from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

MULTI_RELATIONS = frozenset({"VERIFIED_BY", "SUPPORTED_BY"})
SINGLE_RELATIONS = frozenset({"BOUND_TO", "ENFORCED_BY", "DISPATCHED_BY"})
RELATIONS = MULTI_RELATIONS | SINGLE_RELATIONS

@dataclass(frozen=True)
class Relationship:
    source: str
    relation: str
    target: str
    tier: str | None = None
    evidence: str | None = None

def validate_relationships(items: Iterable[Relationship]) -> list[Relationship]:
    rows = list(items)
    for item in rows:
        if item.relation not in RELATIONS:
            raise ValueError(f"INVALID_RELATION:{item.relation}")
    for item in rows:
        if item.relation in SINGLE_RELATIONS:
            targets = {
                x.target for x in rows
                if x.source == item.source and x.relation == item.relation
            }
            if len(targets) > 1:
                raise ValueError(f"AMBIGUOUS_BINDING:{item.source}:{item.relation}")
    return sorted(rows, key=lambda x: (x.source, x.relation, x.target))

def relationship_dict(item: Relationship) -> dict:
    return asdict(item)
