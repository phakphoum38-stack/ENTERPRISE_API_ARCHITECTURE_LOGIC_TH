from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--data", default="{}")
    args = parser.parse_args()

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object]
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {"schema_version": 1, "candidate_status": "in_progress", "stages": {}}

    stages = payload.setdefault("stages", {})
    assert isinstance(stages, dict)
    stages[args.stage] = {
        "status": args.status,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "data": json.loads(args.data),
    }
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)
    print(f"Recorded V3 Clean evidence: {args.stage} = {args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
