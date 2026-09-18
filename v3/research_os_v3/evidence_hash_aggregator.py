from __future__ import annotations
import hashlib, json
from typing import Iterable, Mapping

class EvidenceHashAggregator:
    def hash_entry(self, entry: Mapping) -> str:
        payload=json.dumps(dict(entry),sort_keys=True,separators=(",",":"),ensure_ascii=True)
        return hashlib.sha256(payload.encode()).hexdigest()
    def aggregate(self, entries: Iterable[Mapping]) -> dict:
        rows=list(entries)
        hashes=[self.hash_entry(e) for e in rows]
        return {"count":len(rows),"evidence_hashes":hashes,"manifest_hash":self.hash_entry({"entries":hashes})}