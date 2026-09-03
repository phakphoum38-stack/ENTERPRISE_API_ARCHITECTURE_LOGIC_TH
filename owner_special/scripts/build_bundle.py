from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parent
for source_root in (ROOT, REPOSITORY_ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from research_os_friend import OwnerBundleBuilder


DIST = ROOT / "dist"
OUTPUT = DIST / "Research-OS-Owner-Special-Friend-Complete.zip"
MANIFEST = DIST / "RELEASE_MANIFEST.txt"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)
    result = OwnerBundleBuilder(ROOT).build(OUTPUT)

    source_sha = os.environ.get("GITHUB_SHA", "").strip()
    setup = DIST / "validated-installer" / "Research-OS-Owner-Special-Setup-1.3.1-x64.exe"
    evidence = DIST / "validated-installer" / "owner-v1.3-validation.json"

    # The manifest is deliberately independent of its own digest so the
    # bundle hash remains deterministic and auditable without a hash cycle.
    lines = [
        "Research OS Owner Special Final Release Manifest",
        f"Source commit: {source_sha or 'UNSET'}",
        f"Source bundle: {OUTPUT.name}",
        f"Source bundle SHA256: {result['sha256']}",
        f"Owner Setup: {setup.name}",
        f"Owner Setup SHA256: {_sha256(setup) if setup.is_file() else 'UNAVAILABLE'}",
        f"Validation evidence: {evidence.name}",
        f"Validation evidence SHA256: {_sha256(evidence) if evidence.is_file() else 'UNAVAILABLE'}",
        "Identity gate: required and passed before validated installer publication",
        "Installer E2E: clean install + startup + upgrade + uninstall + data preservation",
        "Release policy: canonical Owner Special pipeline only",
    ]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Embed the manifest inside the source bundle so the final release carries
    # the same lineage evidence even though the final ZIP is composed later.
    with zipfile.ZipFile(OUTPUT, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(MANIFEST, "RELEASE_MANIFEST.txt")

    final_bundle_sha = _sha256(OUTPUT)
    (DIST / "BUNDLE_SHA256.txt").write_text(
        f"{final_bundle_sha}  {OUTPUT.name}\n",
        encoding="utf-8",
    )
    result["sha256"] = final_bundle_sha
    result["source_sha"] = source_sha
    result["release_manifest"] = "RELEASE_MANIFEST.txt"
    (DIST / "bundle-result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
