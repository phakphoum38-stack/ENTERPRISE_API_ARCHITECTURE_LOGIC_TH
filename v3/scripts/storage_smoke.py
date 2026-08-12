from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import DataLayout, UserContext


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="research-os-v3-data-") as temporary:
        layout = DataLayout(Path(temporary)).ensure()

        legacy_marker = layout.sessions / "preservation.marker"
        legacy_marker.write_text("preserve-legacy", encoding="utf-8")

        alice = layout.for_user(UserContext("alice", "default")).ensure()
        bob = layout.for_user(UserContext("bob", "default")).ensure()
        alice_marker = alice.sessions / "preservation.marker"
        alice_marker.write_text("alice-only", encoding="utf-8")

        second = DataLayout(Path(temporary)).ensure()
        alice_again = second.for_user(UserContext("alice", "default")).ensure()
        bob_again = second.for_user(UserContext("bob", "default")).ensure()

        assert legacy_marker.read_text(encoding="utf-8") == "preserve-legacy"
        assert (alice_again.sessions / "preservation.marker").read_text(
            encoding="utf-8"
        ) == "alice-only"
        assert not (bob_again.sessions / "preservation.marker").exists()
        assert alice_again.root != bob_again.root

        for directory in second.directories().values():
            assert directory.is_dir()
        assert second.users.is_dir()
        for user_layout in (alice_again, bob_again):
            for directory in user_layout.directories().values():
                assert directory.is_dir()

        payload = {
            "status": "ok",
            "idempotent": True,
            "preserved_existing_data": True,
            "cross_user_isolation": True,
            "legacy_root_preserved": True,
            "user_a_scope": str(alice_again.root.relative_to(second.root)),
            "user_b_scope": str(bob_again.root.relative_to(second.root)),
            "directories": sorted(alice_again.directories().keys()),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
