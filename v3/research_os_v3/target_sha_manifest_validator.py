from __future__ import annotations
import re
from typing import Mapping

SHA1=re.compile(r"^[0-9a-f]{40}$")
SHA256=re.compile(r"^[0-9a-f]{64}$")

class TargetManifestError(ValueError): pass
class TargetSHAManifestValidator:
    def validate(self, manifest: Mapping) -> None:
        target=manifest.get("target_sha")
        if not isinstance(target,str) or not SHA1.fullmatch(target): raise TargetManifestError("invalid target_sha")
        algorithm=manifest.get("target_identity_algorithm")
        if algorithm not in ("git-sha1",): raise TargetManifestError("unsupported target identity algorithm")
        if manifest.get("evidence_algorithm") != "sha256": raise TargetManifestError("unsupported evidence algorithm")
        entries=manifest.get("entries")
        if not isinstance(entries,list) or not entries: raise TargetManifestError("manifest entries required")
        for entry in entries:
            if entry.get("target_sha") != target: raise TargetManifestError("mixed target_sha")
            evidence=entry.get("evidence_hash")
            if not isinstance(evidence,str) or not SHA256.fullmatch(evidence): raise TargetManifestError("invalid evidence_hash")
        return None
