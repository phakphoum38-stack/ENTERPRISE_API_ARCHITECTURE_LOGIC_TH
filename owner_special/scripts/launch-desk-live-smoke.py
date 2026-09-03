from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_os_friend.launch_desk_agent import stream_launch_desk
from research_os_friend.provider_settings import ProviderManager


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real Launch Desk smoke using the local secure provider credential.")
    parser.add_argument("text", nargs="?", default="Plan the Research OS production launch after QA validation.")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--owner-id", default="owner")
    args = parser.parse_args()

    manager = ProviderManager(args.data_root, args.owner_id)
    provider = manager.provider()
    if provider is None:
        raise SystemExit("Owner provider is not configured; run Provider Test Connection first.")

    events: list[dict[str, object]] = []
    result = stream_launch_desk(
        text=args.text,
        api_key=provider.api_key,
        base_url=provider.base_url,
        model=provider.model,
        emit=lambda event: events.append(event),
    )
    tool_calls = [str(event.get("tool")) for event in events if event.get("type") == "tool_event" and event.get("phase") == "called"]
    print(json.dumps({"result": result, "tool_calls": tool_calls}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
