from __future__ import annotations
from typing import Mapping
class AuthorityPacketError(ValueError): pass
class AuthorityPacketBuilder:
 def build(self,forensic:Mapping,review:Mapping,pre_authority:Mapping)->dict:
  if forensic.get("target_sha") is None: raise AuthorityPacketError("target identity required")
  if review.get("status") != "PASS": raise AuthorityPacketError("independent review not passed")
  if pre_authority.get("status") != "PASS": raise AuthorityPacketError("pre-authority not passed")
  return {"target_sha":forensic["target_sha"],"independent_review":"PASS","pre_authority":"PASS","owner_authority_required":True,"merge_authorized":False}
