from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_os_friend import FriendRequest, FriendRuntime


def main() -> int:
    runtime = FriendRuntime.create_owner_special("owner")
    response = runtime.ask(
        FriendRequest(
            owner_id="owner",
            text="Owner Special Friend Complete smoke",
            complexity=9,
            risk=7,
            parallelism=8,
            requested_skills=("analysis", "planning", "coding", "security", "quality"),
            requested_tools=("echo",),
        )
    )
    payload = {
        "status": "ok",
        "architecture": runtime.architecture(),
        "decision": {
            "scale": response.decision.scale.value,
            "capacity": response.decision.maximum_leaf_capacity,
            "skills": response.decision.selected_skills,
            "tools": response.decision.selected_tools,
        },
        "provider": response.provider,
        "memory_items": response.memory_items,
        "evidence": bool(response.evidence_id),
    }
    assert payload["decision"]["capacity"] == 46656
    assert payload["architecture"]["memory_scope"] == "owner/profile/session"
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
