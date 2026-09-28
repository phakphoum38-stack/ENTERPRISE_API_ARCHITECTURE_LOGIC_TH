from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping

@dataclass(frozen=True)
class IdentityRecord:
    scenario_id: str
    task_id: str
    event_id: str
    delivery_id: str
    idempotency_key: str

class IdentityConservationAggregator:
    REQUIRED = ("task_id","event_id","delivery_id","idempotency_key")
    def validate(self, record: Mapping[str,str]) -> None:
        missing=[k for k in self.REQUIRED if not record.get(k)]
        if missing: raise ValueError(f"missing identity: {missing}")
    def aggregate(self, records: Iterable[Mapping[str,str]]) -> dict:
        rows=list(records)
        for row in rows: self.validate(row)
        keys={(r["task_id"],r["event_id"],r["idempotency_key"]) for r in rows}
        return {"records":len(rows),"unique_logical_identities":len(keys),"duplicate_logical_identity":len(keys)<len(rows),"conserved":all(r["task_id"] and r["event_id"] and r["idempotency_key"] for r in rows)}