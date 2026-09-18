from __future__ import annotations
from typing import Iterable,Mapping
class AssuranceLedger:
 def build(self,target_sha:str,entries:Iterable[Mapping])->dict:
  rows=list(entries)
  return {"protocol":"V3-RUNTIME-10POW1000","target_sha":target_sha,"entry_count":len(rows),"entries":rows,"status":"PASS" if rows and all(e.get("passed") is True for e in rows) else "HOLD"}
