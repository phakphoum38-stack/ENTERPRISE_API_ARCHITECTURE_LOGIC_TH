from __future__ import annotations
from typing import Mapping
class AuthorityBoundaryError(ValueError): pass
class AuthorityBoundary:
 def evaluate(self,packet:Mapping,owner_authorized:bool)->dict:
  if packet.get("owner_authority_required") is not True: raise AuthorityBoundaryError("owner authority requirement missing")
  return {"owner_authority_required":True,"owner_authorized":bool(owner_authorized),"merge_authorized":bool(owner_authorized) and packet.get("pre_authority") == "PASS"}
