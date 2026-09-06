#!/usr/bin/env python3
"""Create a deterministic evidence manifest bound to workflow run and source SHA."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workflow", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--input", action="append", default=[])
    p.add_argument("--metadata", help="JSON object containing verified gate metadata")
    p.add_argument("--output", default=str(REPORTS / "IMMUTABLE_EVIDENCE.json"))
    args = p.parse_args()

    commit = args.commit.strip().lower()
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise SystemExit("invalid commit SHA")

    files = []
    for raw in sorted(args.input):
        path = Path(raw)
        if not path.is_file():
            raise SystemExit(f"evidence file missing: {path}")
        files.append({"path": str(path), "sha256": sha256_file(path)})

    metadata = {}
    if args.metadata:
        metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise SystemExit("metadata must be a JSON object")

    manifest = {
        "version": 1,
        "immutable": True,
        "workflow": args.workflow,
        "run_id": str(args.run_id),
        "commit": commit,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence": files,
        **metadata,
    }
    manifest.pop("manifest_sha256", None)
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["manifest_sha256"] = hashlib.sha256(payload).hexdigest()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
