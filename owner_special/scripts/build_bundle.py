from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parent
for source_root in (ROOT, REPOSITORY_ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from research_os_friend import OwnerBundleBuilder


DIST = ROOT / "dist"
OUTPUT = DIST / "Research-OS-Owner-Special-Friend-Complete.zip"


def main() -> int:
    result = OwnerBundleBuilder(ROOT).build(OUTPUT)
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "BUNDLE_SHA256.txt").write_text(
        f"{result['sha256']}  {OUTPUT.name}\n",
        encoding="utf-8",
    )
    (DIST / "bundle-result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
