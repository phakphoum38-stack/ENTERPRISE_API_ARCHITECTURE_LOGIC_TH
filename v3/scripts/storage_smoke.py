from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3.storage import DataLayout


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="research-os-v3-data-") as temporary:
        layout = DataLayout(Path(temporary)).ensure()
        marker = layout.sessions / "preservation.marker"
        marker.write_text("preserve-me", encoding="utf-8")

        second = DataLayout(Path(temporary)).ensure()
        assert marker.read_text(encoding="utf-8") == "preserve-me"
        for directory in second.directories().values():
            assert directory.is_dir()

        payload = {
            "status": "ok",
            "idempotent": True,
            "preserved_existing_data": True,
            "directories": sorted(second.directories().keys()),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
