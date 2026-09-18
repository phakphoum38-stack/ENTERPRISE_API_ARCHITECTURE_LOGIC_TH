from __future__ import annotations
import hashlib,json
from typing import Mapping
class FinalAssuranceBundleError(ValueError): pass
class FinalAssuranceBundle:
 def build(self,ledger:Mapping,review:Mapping,packet:Mapping,replay:Mapping)->dict:
  target=ledger.get("target_sha")
  if not target or review.get("target_sha")!=target or packet.get("target_sha")!=target: raise FinalAssuranceBundleError("target mismatch")
  if review.get("status")!="PASS" or replay.get("certified") is not True: raise FinalAssuranceBundleError("assurance incomplete")
  body={"target_sha":target,"ledger_hash":ledger.get("ledger_hash"),"review":"PASS","replay":"CERTIFIED","owner_authority_required":True}
  body["bundle_hash"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
  return body
