from __future__ import annotations
from typing import Mapping
class ReplayProofError(ValueError): pass
class CrossSubsystemReplayProof:
 REQUIRED=("task_id","event_id","delivery_id","idempotency_key")
 def verify(self, original:Mapping,replay:Mapping)->dict:
  for key in self.REQUIRED:
   if not original.get(key) or not replay.get(key): raise ReplayProofError(f"missing {key}")
   if original[key]!=replay[key]: raise ReplayProofError(f"identity changed: {key}")
  if replay.get("replay_id")==replay.get("task_id"): raise ReplayProofError("replay_id collides with task_id")
  return {"verified":True,"identity_conserved":True,"logical_task_conserved":True}
