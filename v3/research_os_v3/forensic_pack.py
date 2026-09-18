from __future__ import annotations
import hashlib,json,re
from typing import Iterable
SHA1=re.compile(r"^[0-9a-f]{40}$")
class ForensicPackError(ValueError): pass
class SameSHAForensicPack:
 def build(self,target_sha:str,base_sha:str,files:Iterable[str],evidence_hashes:Iterable[str])->dict:
  if not SHA1.fullmatch(target_sha) or not SHA1.fullmatch(base_sha): raise ForensicPackError("invalid commit sha")
  paths=list(files); hashes=list(evidence_hashes)
  if not paths: raise ForensicPackError("changed files required")
  if len(paths)!=len(set(paths)): raise ForensicPackError("duplicate changed file")
  payload={"base_sha":base_sha,"target_sha":target_sha,"files":sorted(paths),"evidence_hashes":sorted(hashes)}
  canonical=json.dumps(payload,sort_keys=True,separators=(",",":"))
  payload["forensic_hash"]=hashlib.sha256(canonical.encode()).hexdigest()
  return payload
