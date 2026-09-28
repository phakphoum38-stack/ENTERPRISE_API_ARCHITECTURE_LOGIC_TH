from __future__ import annotations
from typing import Mapping
class ReplayCertificationError(ValueError): pass
class ReplayCertification:
 REQUIRED=("task_id","event_id","delivery_id","idempotency_key")
 def certify(self,original:Mapping,replay:Mapping)->dict:
  for k in self.REQUIRED:
   if original.get(k)!=replay.get(k) or not original.get(k): raise ReplayCertificationError(f"identity not conserved: {k}")
  if replay.get("passed") is not True: raise ReplayCertificationError("replay not passed")
  return {"certified":True,"identity_conserved":True,"exactly_once_logical_identity":True}
