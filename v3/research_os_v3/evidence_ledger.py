from __future__ import annotations
import hashlib,json
from typing import Mapping
class EvidenceLedgerError(ValueError): pass
class EvidenceLedger:
 def append(self,ledger:Mapping,entry:Mapping)->dict:
  rows=list(ledger.get("entries",[])); rows.append(dict(entry))
  payload={"target_sha":ledger.get("target_sha"),"entries":rows}
  if not payload["target_sha"]: raise EvidenceLedgerError("target_sha required")
  canonical=json.dumps(payload,sort_keys=True,separators=(",",":"))
  return {**payload,"ledger_hash":hashlib.sha256(canonical.encode()).hexdigest()}
