from __future__ import annotations
from typing import Iterable,Mapping
class EvidenceReconciliationError(ValueError): pass
class RuntimeEvidenceReconciler:
 def reconcile(self, entries:Iterable[Mapping],target_sha:str)->dict:
  rows=list(entries)
  if not rows: raise EvidenceReconciliationError("no evidence")
  failures=[]
  for e in rows:
   if e.get("target_sha")!=target_sha: failures.append("target_mismatch")
   if e.get("passed") is not True: failures.append("not_passed")
   if not e.get("evidence_hash"): failures.append("missing_hash")
  return {"target_sha":target_sha,"entries":len(rows),"failures":sorted(set(failures)),"reconciled":not failures}
